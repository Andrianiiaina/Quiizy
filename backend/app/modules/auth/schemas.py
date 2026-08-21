from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100, strip_whitespace=True)
    last_name: str = Field(min_length=1, max_length=100, strip_whitespace=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)
