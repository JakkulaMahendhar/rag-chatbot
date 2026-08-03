from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):

    email: EmailStr

    password: str = Field(min_length=8, max_length=72)


class UserResponse(BaseModel):

    id: int

    email: EmailStr

    is_active: bool

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):

    email: EmailStr

    password: str


class TokenResponse(BaseModel):

    access_token: str

    token_type: str = "bearer"
