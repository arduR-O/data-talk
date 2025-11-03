from pydantic import BaseModel, EmailStr, Field

class SignupRequest(BaseModel):
    firstName: str = Field(..., min_length=1, max_length=50)
    lastName: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    user_id: str
    email: str
    firstName: str
    lastName: str

class AuthResponse(BaseModel):
    message: str
    data: dict

class ErrorResponse(BaseModel):
    detail: str