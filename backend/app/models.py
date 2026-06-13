"""SQLAlchemy ORM models for OralDysplasia AI."""

import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    license_id = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)          # Consultant Pathologist | Resident | Lab Tech
    institution = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    slides = relationship("Slide", back_populates="owner")
    annotations = relationship("Annotation", back_populates="pathologist")


class Slide(Base):
    __tablename__ = "slides"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Patient info — encrypted at rest via AES-256
    patient_id_enc = Column(String(255), nullable=False)
    patient_name_enc = Column(String(255), nullable=False)
    patient_age_enc = Column(String(255), nullable=True)
    patient_gender_enc = Column(String(255), nullable=True)

    anatomical_site = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=True)
    size_bytes = Column(Integer, default=0)
    width = Column(Integer, default=2048)
    height = Column(Integer, default=2048)

    status = Column(String(255), default="uploaded")       # uploaded | preprocessing | ready | analyzing | processed | error
    current_grade = Column(String(255), default="pending")  # pending | normal | mild | moderate | severe
    overall_confidence = Column(Float, default=0.0)
    clinical_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="slides")
    patches = relationship("Patch", back_populates="slide", cascade="all, delete-orphan")
    annotations = relationship("Annotation", back_populates="slide", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="slide", cascade="all, delete-orphan")


class Patch(Base):
    __tablename__ = "patches"

    id = Column(Integer, primary_key=True, index=True)
    slide_id = Column(Integer, ForeignKey("slides.id", ondelete="CASCADE"), nullable=False)
    x_index = Column(Integer, nullable=False)
    y_index = Column(Integer, nullable=False)

    confidence_mild = Column(Float, default=0.0)
    confidence_moderate = Column(Float, default=0.0)
    confidence_severe = Column(Float, default=0.0)
    confidence_normal = Column(Float, default=1.0)
    predicted_grade = Column(String(255), default="normal")

    # [{xmin, ymin, xmax, ymax, grade, confidence}, ...]
    bounding_boxes = Column(JSON, nullable=True)

    slide = relationship("Slide", back_populates="patches")


class Annotation(Base):
    __tablename__ = "annotations"

    id = Column(Integer, primary_key=True, index=True)
    slide_id = Column(Integer, ForeignKey("slides.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    shape_data = Column(JSON, nullable=False)       # Polygon coordinates + labels
    final_grade = Column(String(255), nullable=False)
    comments = Column(Text, nullable=True)
    icd_10_code = Column(String(255), default="K13.29")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    slide = relationship("Slide", back_populates="annotations")
    pathologist = relationship("User", back_populates="annotations")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    slide_id = Column(Integer, ForeignKey("slides.id", ondelete="CASCADE"), nullable=False)
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    format = Column(String(255), nullable=False)          # pdf | dicom | fhir
    report_payload = Column(JSON, nullable=False)
    generated_at = Column(DateTime, default=datetime.datetime.utcnow)

    slide = relationship("Slide", back_populates="reports")
