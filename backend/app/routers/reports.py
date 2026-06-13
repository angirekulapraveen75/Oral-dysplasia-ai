"""Reports router — export diagnostic reports (FHIR / DICOM / PDF payload)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import decrypt_pii
from app.database import get_db
from app.models import Annotation, Report, Slide, User
from app.schemas import ReportResponse
from app.routers.slides import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/{slide_id}/export", response_model=ReportResponse)
async def export_report(
    slide_id: int,
    format: str = Query("fhir", enum=["pdf", "dicom", "fhir", "patient_pdf"]),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Slide).where(Slide.id == slide_id))
    slide = result.scalars().first()
    if not slide:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Slide not found")

    patient_name = decrypt_pii(slide.patient_name_enc)
    patient_id = decrypt_pii(slide.patient_id_enc)
    patient_age = decrypt_pii(slide.patient_age_enc) if slide.patient_age_enc else "N/A"
    patient_gender = decrypt_pii(slide.patient_gender_enc) if slide.patient_gender_enc else "N/A"

    # Latest annotation
    anno_q = await db.execute(
        select(Annotation).where(Annotation.slide_id == slide_id)
        .order_by(Annotation.created_at.desc())
    )
    anno = anno_q.scalars().first()
    icd10 = anno.icd_10_code if anno else "K13.29"
    comments = anno.comments if anno else ""

    current_grade = slide.current_grade or "pending"

    # Build payload based on format
    if format == "fhir":
        payload = {
            "resourceType": "DiagnosticReport",
            "status": "final",
            "code": {"text": "Oral Dysplasia AI Grading Report"},
            "subject": {"display": f"{patient_name} (Age: {patient_age}, Gender: {patient_gender})", "reference": f"Patient/{patient_id}"},
            "result": [{"display": f"{current_grade} Oral Epithelial Dysplasia"}],
            "conclusion": f"Grade: {current_grade}. Confidence: {slide.overall_confidence}. {comments}",
            "conclusionCode": [{"coding": [{"system": "icd-10", "code": icd10}]}],
        }
    elif format == "dicom":
        payload = {
            "SOPClassUID": "1.2.840.10008.5.1.4.1.1.88.33",
            "PatientName": patient_name,
            "PatientID": patient_id,
            "PatientAge": patient_age,
            "PatientSex": patient_gender,
            "DocumentTitle": "Oral Dysplasia AI Diagnosis",
            "Grade": current_grade,
            "Confidence": slide.overall_confidence,
            "ICD10": icd10,
            "SignedBy": user.name,
        }
    elif format == "patient_pdf":
        grade_explanations = {
            "normal": "No signs of oral epithelial dysplasia were found (Benign / Normal tissue).",
            "mild": "Mild dysplasia detected. Cell alterations are confined to the lower third of the epithelium. Standard monitoring and follow-up recommended.",
            "moderate": "Moderate dysplasia detected. Cell alterations extend to the middle third of the epithelium. Close clinical observation or intervention may be required.",
            "severe": "Severe dysplasia / Carcinoma in situ detected. Cell alterations occupy the upper third or full thickness of the epithelium. Prompt clinical treatment is required.",
            "pending": "Analysis is pending verification."
        }
        explanation = grade_explanations.get(current_grade.lower(), "Verification required by pathologist.")
        payload = {
            "type": "Patient Diagnostic Report",
            "patient": {
                "name": patient_name,
                "id": patient_id,
                "age": patient_age,
                "gender": patient_gender,
                "site": slide.anatomical_site
            },
            "diagnosis": {
                "grade": current_grade.upper(),
                "explanation": explanation,
                "next_steps": "Please consult your oral surgeon or primary clinician to discuss these diagnostic findings."
            },
            "signed_by": f"Dr. {user.name} ({user.role})",
            "institution": user.institution
        }
    else:  # pdf
        payload = {
            "type": "PDF Diagnostic Report",
            "patient": {"name": patient_name, "id": patient_id, "age": patient_age, "gender": patient_gender, "site": slide.anatomical_site},
            "slide": {"filename": slide.filename, "dimensions": f"{slide.width}x{slide.height}"},
            "diagnosis": {"grade": current_grade, "confidence": slide.overall_confidence, "icd10": icd10},
            "signed_by": user.name,
            "comments": comments,
        }

    report = Report(
        slide_id=slide.id, generated_by=user.id,
        format=format, report_payload=payload,
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)

    return ReportResponse(report_id=report.id, format=format, payload=payload)
