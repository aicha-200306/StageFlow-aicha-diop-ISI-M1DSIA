from pydantic import BaseModel, EmailStr

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role_id: int
    role_name: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"