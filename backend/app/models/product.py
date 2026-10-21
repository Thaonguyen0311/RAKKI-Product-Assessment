from datetime import date, datetime
from sqlalchemy import String, Text, DateTime, Date, ForeignKey, Numeric, JSON, Integer, Boolean, BigInteger, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

class Product(Base):
    __tablename__ = 'products'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180), default='', nullable=False)
    category: Mapped[str | None] = mapped_column(String(80))
    location: Mapped[str | None] = mapped_column(String(180))
    completion_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    overall_condition: Mapped[int | None] = mapped_column(Integer)
    is_intact: Mapped[bool | None] = mapped_column(Boolean)
    is_clean: Mapped[bool | None] = mapped_column(Boolean)
    quantity: Mapped[int] = mapped_column(Integer, default=1, server_default='1', nullable=False)
    additional_notes: Mapped[str | None] = mapped_column(Text)
    process: Mapped[str | None] = mapped_column(String(180))
    process_id: Mapped[str | None] = mapped_column(String(20))
    material: Mapped[str | None] = mapped_column(String(180))
    material_id: Mapped[int | None] = mapped_column(BigInteger)
    material_category: Mapped[str | None] = mapped_column(Text)
    material_verification: Mapped[str | None] = mapped_column(String(30))
    material_confidence: Mapped[float | None] = mapped_column(Numeric(4, 3))
    ai_status: Mapped[str] = mapped_column(String(30), default='not_started')
    assessment_status: Mapped[str] = mapped_column(String(40), default='incomplete')
    field_provenance: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    field_verification: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    materials: Mapped[list['Material']] = relationship(cascade='all, delete-orphan')
    images: Mapped[list['ProductImage']] = relationship(cascade='all, delete-orphan')

class Material(Base):
    __tablename__ = 'product_materials'
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id', ondelete='CASCADE'), index=True)
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str | None] = mapped_column(String(80))
    percentage: Mapped[float | None] = mapped_column(Numeric(5,2))
    provenance: Mapped[str] = mapped_column(String(30), default='user_input')
    verification: Mapped[str] = mapped_column(String(30), default='unverified')
    evidence: Mapped[str | None] = mapped_column(Text)

class ProductImage(Base):
    __tablename__ = 'product_images'
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id', ondelete='CASCADE'), index=True)
    filename: Mapped[str] = mapped_column(String(100), unique=True)
    content_type: Mapped[str] = mapped_column(String(40))
    size_bytes: Mapped[int] = mapped_column(Integer)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class AIExtraction(Base):
    __tablename__ = 'ai_extractions'
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id', ondelete='CASCADE'), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(30))
    model: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class Assessment(Base):
    __tablename__ = 'assessment_results'
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id', ondelete='CASCADE'), index=True)
    kind: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(40))
    result: Mapped[float | None] = mapped_column(Numeric(12,4))
    unit: Mapped[str | None] = mapped_column(String(60))
    methodology: Mapped[str | None] = mapped_column(String(200))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class Revision(Base):
    __tablename__ = 'product_revisions'
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id', ondelete='CASCADE'), index=True)
    snapshot: Mapped[dict] = mapped_column(JSON)
    changed_fields: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class EvidenceSource(Base):
    __tablename__ = 'evidence_sources'
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id', ondelete='CASCADE'), index=True)
    label: Mapped[str] = mapped_column(String(160))
    source_type: Mapped[str] = mapped_column(String(30))
    reference: Mapped[str | None] = mapped_column(Text)
    verification: Mapped[str] = mapped_column(String(30), default='unverified')
