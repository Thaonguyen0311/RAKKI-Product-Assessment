from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field, model_validator

class Provenance(StrEnum):
    image_observation='image_observation'; user_input='user_input'; manufacturer_source='manufacturer_source'; external_dataset='external_dataset'; ai_inference='ai_inference'; calculated='calculated'
class Verification(StrEnum):
    unverified='unverified'; verified='verified'; rejected='rejected'; not_applicable='not_applicable'

class MaterialIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str | None = None
    percentage: float | None = Field(default=None, ge=0, le=100)
    provenance: Provenance = Provenance.user_input
    verification: Verification = Verification.unverified
    evidence: str | None = None

class ProductIn(BaseModel):
    name: str = Field(default='Untitled product', min_length=1, max_length=180)
    category: str | None = None
    subtype: str | None = None
    brand: str | None = None
    sku: str | None = None
    color: str | None = None
    description: str | None = None
    condition: str | None = None
    materials: list[MaterialIn] = []

    @model_validator(mode='after')
    def total_percentage(self):
        total = sum(m.percentage or 0 for m in self.materials)
        if total > 100.01: raise ValueError('Material percentages cannot exceed 100%')
        return self

class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=180)
    category: str | None = None; subtype: str | None = None; brand: str | None = None
    sku: str | None = None; color: str | None = None; description: str | None = None; condition: str | None = None

class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; name: str; category: str | None; subtype: str | None; brand: str | None; sku: str | None
    color: str | None; description: str | None; condition: str | None; ai_status: str; assessment_status: str
    created_at: object; updated_at: object

class VerifyIn(BaseModel):
    verification: Verification
    reviewer_note: str | None = None
