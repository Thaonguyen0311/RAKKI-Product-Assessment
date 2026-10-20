from enum import StrEnum
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator
from app.services.materials import validated_material

CATEGORY_OPTIONS = (
    'Movable Furniture and Fixed Furnishings',
    'Electrical',
    'HVAC and Plumbing',
    'Building Components and Materials',
    'Other',
)

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
    name: str = Field(default='', max_length=180, validation_alias=AliasChoices('name', 'product_name'))
    category: str | None = None
    location: str | None = Field(default=None, max_length=180)
    overall_condition: int | None = Field(default=None, ge=1, le=5, strict=True)
    is_intact: bool | None = None
    is_clean: bool | None = None
    quantity: int = Field(default=1, ge=1, strict=True)
    additional_notes: str | None = None
    subtype: str | None = None
    brand: str | None = None
    sku: str | None = None
    color: str | None = None
    description: str | None = None
    condition: str | None = None
    material: str | None = None
    materials: list[MaterialIn] = Field(default_factory=list)

    @field_validator('category')
    @classmethod
    def validate_category(cls, value):
        if value is not None and value not in CATEGORY_OPTIONS:
            raise ValueError('Select one of the available product categories')
        return value

    @field_validator('material')
    @classmethod
    def validate_material(cls, value):
        return validated_material(value)

    @model_validator(mode='after')
    def total_percentage(self):
        total = sum(m.percentage or 0 for m in self.materials)
        if total > 100.01: raise ValueError('Material percentages cannot exceed 100%')
        return self

class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=180, validation_alias=AliasChoices('name', 'product_name'))
    category: str | None = None
    location: str | None = Field(default=None, max_length=180)
    overall_condition: int | None = Field(default=None, ge=1, le=5, strict=True)
    is_intact: bool | None = None
    is_clean: bool | None = None
    quantity: int = Field(default=1, ge=1, strict=True)
    additional_notes: str | None = None
    subtype: str | None = None; brand: str | None = None
    sku: str | None = None; color: str | None = None; description: str | None = None; condition: str | None = None
    material: str | None = None
    materials: list[MaterialIn] | None = None

    @field_validator('name')
    @classmethod
    def name_cannot_be_null(cls, value):
        if value is None:
            raise ValueError('Product name may be empty but cannot be null')
        return value

    @field_validator('material')
    @classmethod
    def validate_material(cls, value):
        return validated_material(value)

class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; name: str; category: str | None; location: str | None; completion_date: object
    overall_condition: int | None; is_intact: bool | None; is_clean: bool | None; quantity: int; additional_notes: str | None
    subtype: str | None; brand: str | None; sku: str | None
    material: str | None = None; material_id: int | None = None; material_category: str | None = None
    material_verification: str | None = None; material_confidence: float | None = None
    color: str | None; description: str | None; condition: str | None; ai_status: str; assessment_status: str
    field_provenance: dict[str, str] = Field(default_factory=dict); field_verification: dict[str, str] = Field(default_factory=dict)
    created_at: object; updated_at: object

    @computed_field
    @property
    def product_name(self) -> str:
        return self.name


class AIProductSuggestion(BaseModel):
    model_config = ConfigDict(extra='forbid')
    product_name: str | None = Field(default=None, max_length=180)
    category: str | None = None
    additional_notes: str | None = None
    suggested_material: str | None = Field(default=None, max_length=180)
    material_confidence: float = Field(default=0, ge=0, le=1)
    overall_condition: None = None
    is_intact: None = None
    is_clean: None = None
    confidence: float = Field(default=0, ge=0, le=1)

    @field_validator('category')
    @classmethod
    def validate_category(cls, value):
        if value is not None and value not in CATEGORY_OPTIONS:
            raise ValueError('AI returned a category outside the supported options')
        return value

class VerifyIn(BaseModel):
    verification: Verification
    reviewer_note: str | None = None
