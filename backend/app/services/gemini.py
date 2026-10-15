import json
import mimetypes
from google import genai
from google.genai import types
from app.core.config import settings

def analyze_image(path: str) -> dict:
    if not settings.gemini_api_key:
        raise RuntimeError('AI analysis is not configured. Add GEMINI_API_KEY to backend/.env.')
    client = genai.Client(api_key=settings.gemini_api_key, http_options=types.HttpOptions(timeout=30000))
    prompt = '''Analyze only observable facts from this fashion product photo. Return JSON with name, category, subtype, brand, sku, color, description, condition, and materials (array of name/category/percentage). Never infer fiber composition, sustainability claims, manufacturing origin or lifespan from the image. Set unsupported fields to null. Mark observation-only.'''
    mime_type, _ = mimetypes.guess_type(path)
    # response = client.models.generate_content(model=settings.gemini_model, contents=[prompt, types.Part.from_bytes(data=open(path,'rb').read(), mime_type=mime_type)], config=types.GenerateContentConfig(response_mime_type='application/json'))
    # try: data = json.loads(response.text or '{}')
    # except Exception as exc: raise ValueError('AI returned an invalid structured response') from exc
    # if not isinstance(data, dict): raise ValueError('AI returned an invalid structured response')
    # allowed={'name','category','subtype','brand','sku','color','description','condition','materials'}
    # return {k:v for k,v in data.items() if k in allowed}

    mime_type = mimetypes.guess_type(path)[0]

    if mime_type not in ('image/jpeg', 'image/png', 'image/webp'):
        raise ValueError(f'Unsupported image MIME type: {mime_type}')

    with open(path, 'rb') as image_file:
        image_data = image_file.read()

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=[
            prompt,
            types.Part.from_bytes(
                data=image_data,
                mime_type=mime_type
            )
        ],
        config=types.GenerateContentConfig(
            response_mime_type='application/json'
        )
    )
