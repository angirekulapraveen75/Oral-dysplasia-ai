"""Pydantic schemas — single source of truth for API contracts."""

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


# ━━ Auth ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: str
    license_id: str
    role: str        # Consultant Pathologist | Resident | Lab Tech
    institution: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserBrief


class UserBrief(BaseModel):
    id: int
    name: str
    email: str
    role: str
    institution: str
    license_id: str

    class Config:
        from_attributes = True


# ━━ Slides ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class SlideResponse(BaseModel):
    id: int
    user_id: int
    patient_id: str
    patient_name: str
    patient_age: Optional[str] = None
    patient_gender: Optional[str] = None
    anatomical_site: str
    filename: str
    size_bytes: int
    width: int
    height: int
    status: str
    current_grade: str
    overall_confidence: float
    clinical_notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SlideListResponse(BaseModel):
    slides: List[SlideResponse]
    total: int
    page: int
    limit: int


# ━━ Bounding Boxes & Patches ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class BoundingBox(BaseModel):
    xmin: float
    ymin: float
    xmax: float
    ymax: float
    grade: str
    confidence: float
    label: Optional[str] = None


class PatchResult(BaseModel):
    id: int
    slide_id: int
    x_index: int
    y_index: int
    confidence_mild: float
    confidence_moderate: float
    confidence_severe: float
    confidence_normal: float
    predicted_grade: str
    bounding_boxes: List[BoundingBox] = []

    class Config:
        from_attributes = True


# ━━ Analysis ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class AnalysisRunRequest(BaseModel):
    slide_id: int
    model_version: str = "Swin-T Hybrid v2.1"
    confidence_threshold: float = Field(0.5, ge=0.0, le=1.0)


class AnalysisRunResponse(BaseModel):
    slide_id: int
    status: str
    model_version: str
    confidence_threshold: float


class AnalysisResultResponse(BaseModel):
    slide_id: int
    overall_grade: str
    overall_confidence: float
    total_patches: int
    patches: List[PatchResult]


# ━━ Review / Annotation ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ReviewRequest(BaseModel):
    annotations: List[Dict[str, Any]]
    final_grade: str
    comments: Optional[str] = None
    icd_10_code: str = "K13.29"


class ReviewResponse(BaseModel):
    status: str
    slide_id: int
    final_grade: str
    icd_10_code: str
    signed_by: str


# ━━ Reports ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ReportResponse(BaseModel):
    report_id: int
    format: str
    payload: Dict[str, Any]


# ━━ Dashboard ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class DashboardStats(BaseModel):
    total_slides: int
    pending_review: int
    severe_count: int
    mild_count: int
    moderate_count: int
    recent_slides: List[SlideResponse]


# Forward ref resolution
AuthResponse.model_rebuild()
