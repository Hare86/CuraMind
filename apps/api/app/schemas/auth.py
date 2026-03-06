from pydantic import BaseModel, EmailStr, Field


SALUTATION_CHOICES = ["Mr.", "Ms.", "Mrs.", "Dr.", "Prof.", "Rev."]

ROLE_CHOICES = ["student", "psychologist", "rehab_staff", "hospital_admin", "researcher", "doctor"]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    username: str = Field(min_length=3, max_length=64)
    full_name: str | None = None
    salutation: str | None = None
    role_request: str | None = None  # optional requested role; defaults to "student"


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    username: str | None = None
    full_name: str | None = None
    role: str | None = None
    # For student registration: signal frontend to redirect to login
    requires_login: bool = False
    # For non-student: signal pending approval
    pending_approval: bool = False
