import io, json, uuid
from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Query
from fastapi.responses import StreamingResponse
from PIL import Image, UnidentifiedImageError
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from app.db.session import get_db
from app.models.product import Product, Material, ProductImage, AIExtraction, Assessment, Revision
from app.schemas.product import ProductIn, ProductOut, ProductUpdate, VerifyIn
from app.core.config import settings
from app.services.assessment import carbon_assessment, rapu_assessment
import logging
router=APIRouter(prefix='/api')
@router.get('/health')
def health(db: Session=Depends(get_db)):
    try: db.execute(select(1)); return {'status':'ok','database':'connected'}
    except Exception: raise HTTPException(503,'Database unavailable')
def snapshot(p): return {'id':p.id,'name':p.name,'category':p.category,'subtype':p.subtype,'brand':p.brand,'sku':p.sku,'color':p.color,'description':p.description,'condition':p.condition}
@router.post('/products',response_model=ProductOut,status_code=201)
def create_product(data:ProductIn,db:Session=Depends(get_db)):
    p=Product(**data.model_dump(exclude={'materials'})); p.materials=[Material(**m.model_dump()) for m in data.materials]; db.add(p); db.commit(); db.refresh(p); return p
@router.get('/products')
def list_products(q:str|None=None,status:str|None=None,offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=100),db:Session=Depends(get_db)):
    stmt=select(Product)
    if q: stmt=stmt.where(or_(Product.name.like(f'%{q}%'),Product.brand.like(f'%{q}%'),Product.sku.like(f'%{q}%'),Product.category.like(f'%{q}%')))
    if status: stmt=stmt.where(Product.assessment_status==status)
    rows=db.scalars(stmt.order_by(Product.updated_at.desc()).offset(offset).limit(limit)).all()
    return [{'product':ProductOut.model_validate(p).model_dump(mode='json'),'materials':[{'name':m.name,'category':m.category,'percentage':float(m.percentage) if m.percentage is not None else None,'provenance':m.provenance,'verification':m.verification} for m in p.materials],'images':[i.filename for i in p.images]} for p in rows]
@router.get('/products/{product_id}')
def get_product(product_id:int,db:Session=Depends(get_db)):
    p=db.get(Product,product_id)
    if not p: raise HTTPException(404,'Product not found')
    return {'product':ProductOut.model_validate(p).model_dump(mode='json'),'materials':[{'id':m.id,'name':m.name,'category':m.category,'percentage':float(m.percentage) if m.percentage is not None else None,'provenance':m.provenance,'verification':m.verification,'evidence':m.evidence} for m in p.materials],'images':[{'id':i.id,'filename':i.filename,'content_type':i.content_type} for i in p.images]}
@router.patch('/products/{product_id}',response_model=ProductOut)
def update_product(product_id:int,data:ProductUpdate,db:Session=Depends(get_db)):
    p=db.get(Product,product_id)
    if not p: raise HTTPException(404,'Product not found')
    changes=data.model_dump(exclude_unset=True); changed=[k for k,v in changes.items() if getattr(p,k)!=v]
    if changed:
        db.add(Revision(product_id=p.id,snapshot=snapshot(p),changed_fields=changed))
        for k,v in changes.items(): setattr(p,k,v)
        db.commit(); db.refresh(p)
    return p
@router.post('/products/{product_id}/images',status_code=201)
async def upload(product_id:int,file:UploadFile=File(...),db:Session=Depends(get_db)):
    p=db.get(Product,product_id)
    if not p: raise HTTPException(404,'Product not found')
    data=await file.read(settings.max_upload_size_mb*1024*1024+1)
    if not data or len(data)>settings.max_upload_size_mb*1024*1024: raise HTTPException(413,'Image is empty or exceeds the upload size limit')
    try:
        im=Image.open(io.BytesIO(data)); fmt=im.format
        if fmt not in ('JPEG','PNG','WEBP'): raise ValueError()
        im.verify()
    except (UnidentifiedImageError,OSError,ValueError): raise HTTPException(415,'Upload a valid JPEG, PNG, or WebP image')
    ext={'JPEG':'jpg','PNG':'png','WEBP':'webp'}[fmt]; name=f'{uuid.uuid4().hex}.{ext}'; root=Path(settings.storage_dir).resolve(); root.mkdir(parents=True,exist_ok=True); (root/name).write_bytes(data)
    img=ProductImage(product_id=p.id,filename=name,content_type=f'image/{ext}',size_bytes=len(data)); db.add(img); db.commit(); db.refresh(img)
    return {'id':img.id,'filename':name,'size_bytes':len(data),'status':'uploaded'}
@router.post('/products/{product_id}/analyze')
def analyze(product_id:int,db:Session=Depends(get_db)):
    p=db.get(Product,product_id)
    if not p: raise HTTPException(404,'Product not found')
    img=p.images[-1] if p.images else None
    if not img: raise HTTPException(400,'Upload an image before analysis')
    p.ai_status='processing'; db.commit()
    try:
        from app.services.gemini import analyze_image
        result=analyze_image(str(Path(settings.storage_dir).resolve()/img.filename))
        for key in ('name','category','subtype','brand','sku','color','description','condition'):
            if result.get(key) and not getattr(p,key): setattr(p,key,result[key])
        p.ai_status='completed'; db.add(AIExtraction(product_id=p.id,payload=result,status='completed',model=settings.gemini_model)); db.commit()
        return {'status':'completed','data':result,'provenance':'ai_inference','verification':'unverified'}
    # except Exception as exc:
    #     p.ai_status='failed'; db.commit(); message=str(exc) if isinstance(exc,RuntimeError) else 'Image analysis failed. Retry later.'; raise HTTPException(503,message)
    except Exception as exc:
        logging.exception(
            "Image analysis failed for product %s",
            product_id,
        )

        p.ai_status = "failed"
        db.commit()

        message = (
            str(exc)
            if isinstance(exc, RuntimeError)
            else "Image analysis failed. Check the backend terminal."
        )

        raise HTTPException(
            status_code=503,
            detail=message,
        ) from exc

@router.post('/products/{product_id}/assessments')
def assess(product_id:int,db:Session=Depends(get_db)):
    p=db.get(Product,product_id)
    if not p: raise HTTPException(404,'Product not found')
    out=[]
    for result in (carbon_assessment(p),rapu_assessment(p)):
        db.add(Assessment(product_id=p.id,kind=result['kind'],status=result['status'],result=result['result'],unit=result['unit'],methodology=result['methodology'],details=result['details'])); out.append(result)
    db.commit(); return out
@router.get('/products/{product_id}/revisions')
def revisions(product_id:int,db:Session=Depends(get_db)):
    if not db.get(Product,product_id): raise HTTPException(404,'Product not found')
    return [{'id':r.id,'snapshot':r.snapshot,'changed_fields':r.changed_fields,'created_at':r.created_at.isoformat()} for r in db.scalars(select(Revision).where(Revision.product_id==product_id).order_by(Revision.created_at.desc())).all()]
@router.post('/products/{product_id}/materials/{material_id}/verify')
def verify(product_id:int,material_id:int,data:VerifyIn,db:Session=Depends(get_db)):
    m=db.get(Material,material_id)
    if not m or m.product_id!=product_id: raise HTTPException(404,'Material not found')
    m.verification=data.verification.value; m.evidence=data.reviewer_note; db.add(Revision(product_id=product_id,snapshot={'material_id':m.id,'verification':m.verification,'note':m.evidence},changed_fields=['material.verification'])); db.commit(); return {'status':m.verification}
def safe_cell(value):
    if isinstance(value,str) and value.startswith(('=','+','-','@','\t','\r')): return "'"+value
    return value if value is not None else 'Unknown'
@router.get('/export.xlsx')
def export_products(db:Session=Depends(get_db)):
    products=db.scalars(select(Product).order_by(Product.id)).all(); wb=Workbook(); summary=wb.active; summary.title='Product summary'; summary.append(['ID','Name','Category','Subtype','Brand','SKU','Color','Condition','AI status','Assessment status'])
    mats=wb.create_sheet('Material composition'); mats.append(['Product ID','Product','Material','Category','Percentage by weight','Provenance','Verification','Evidence'])
    sust=wb.create_sheet('Sustainability'); sust.append(['Product ID','Product','Assessment','Status','Result','Unit','Methodology','Details'])
    ev=wb.create_sheet('Evidence'); ev.append(['Product ID','Product','Image','Reference','Verification'])
    for p in products:
        summary.append([safe_cell(x) for x in [p.id,p.name,p.category,p.subtype,p.brand,p.sku,p.color,p.condition,p.ai_status,p.assessment_status]])
        for m in p.materials: mats.append([safe_cell(x) for x in [p.id,p.name,m.name,m.category,m.percentage,m.provenance,m.verification,m.evidence]])
        for a in db.scalars(select(Assessment).where(Assessment.product_id==p.id)): sust.append([safe_cell(x) for x in [p.id,p.name,a.kind,a.status,a.result,a.unit,a.methodology,json.dumps(a.details)]])
        for image in p.images: ev.append([safe_cell(x) for x in [p.id,p.name,image.filename,None,'unverified']])
    for ws in wb.worksheets:
        ws.freeze_panes='A2'; ws.auto_filter.ref=ws.dimensions
        for col in ws.columns: ws.column_dimensions[get_column_letter(col[0].column)].width=min(42,max(12,max((len(str(c.value or '')) for c in col),default=10)+2))
    output=io.BytesIO(); wb.save(output); output.seek(0)
    return StreamingResponse(output,media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',headers={'Content-Disposition':'attachment; filename="rakki-products.xlsx"'})
