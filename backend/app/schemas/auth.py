from pydantic import BaseModel, Field, field_validator


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=5, max_length=256)

    @field_validator('username')
    @classmethod
    def normalize_username(cls, value: str) -> str:
        value = value.strip().casefold()
        if not value:
            raise ValueError('Username is required')
        return value


class UserOut(BaseModel):
    id: int
    username: str
    is_active: bool
    created_at: str
