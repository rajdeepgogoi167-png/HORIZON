from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.compression import jpeg_quality_for_bandwidth, save_compressed
from app.database import get_db
from app.deps import get_current_user
from app.models import Consultation, MedicalRecord, Patient, User

router = APIRouter(prefix="/records", tags=["records"])


def _can_see_patient(user: User, patient_id: int, db: Session) -> bool:
    if user.role == "patient":
        return user.patient_id == patient_id
    if user.role == "doctor" and user.doctor_id:
        return (
            db.query(Consultation)
            .filter(Consultation.doctor_id == user.doctor_id, Consultation.patient_id == patient_id)
            .first()
            is not None
        )
    return user.role == "hospital"


def _can_see_consultation(user: User, consultation: Consultation) -> bool:
    if user.role == "patient":
        return consultation.patient_id == user.patient_id
    if user.role == "doctor":
        return consultation.doctor_id == user.doctor_id
    return user.role == "hospital"


def _record_payload(item: MedicalRecord) -> dict:
    return {
        "id": item.id,
        "original_name": item.original_name,
        "original_bytes": item.original_bytes,
        "compressed_bytes": item.compressed_bytes,
        "consultation_id": item.consultation_id,
        "mime_type": item.mime_type,
    }


@router.post("")
async def upload_record(
    patient_id: int | None = Form(default=None),
    consultation_id: int | None = Form(default=None),
    bandwidth_kbps: float = Form(default=64),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    pid = patient_id or user.patient_id
    if user.role == "patient":
        pid = user.patient_id
    if not pid or not db.get(Patient, pid):
        raise HTTPException(status_code=404, detail="Patient not found")
    if not _can_see_patient(user, pid, db):
        raise HTTPException(status_code=403, detail="Not allowed to upload for this patient")
    consultation = db.get(Consultation, consultation_id) if consultation_id else None
    if consultation_id and not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    if consultation and not _can_see_consultation(user, consultation):
        raise HTTPException(status_code=403, detail="Not your consultation")

    raw = await file.read()
    quality = jpeg_quality_for_bandwidth(bandwidth_kbps)
    path, compressed_size = save_compressed(
        raw,
        file.filename or "record.bin",
        file.content_type or "application/octet-stream",
        quality,
    )
    record = MedicalRecord(
        patient_id=pid,
        consultation_id=consultation_id,
        original_name=file.filename or "record.bin",
        stored_path=str(path),
        mime_type=file.content_type or "application/octet-stream",
        original_bytes=len(raw),
        compressed_bytes=compressed_size,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    saved = max(len(raw) - compressed_size, 0)
    return {
        **_record_payload(record),
        "bytes_saved": saved,
        "ratio": round(compressed_size / len(raw), 3) if raw else 0,
        "jpeg_quality": quality,
    }


@router.get("/consultation/{consultation_id}")
def list_consultation_records(
    consultation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    consultation = db.get(Consultation, consultation_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    if not _can_see_consultation(user, consultation):
        raise HTTPException(status_code=403, detail="Not your consultation")
    records = db.query(MedicalRecord).filter(MedicalRecord.consultation_id == consultation_id).all()
    return [_record_payload(item) for item in records]


@router.get("/patient/{patient_id}")
def list_records(
    patient_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not db.get(Patient, patient_id):
        raise HTTPException(status_code=404, detail="Patient not found")
    if not _can_see_patient(user, patient_id, db):
        raise HTTPException(status_code=403, detail="Not allowed to view these records")
    records = db.query(MedicalRecord).filter(MedicalRecord.patient_id == patient_id).all()
    return [_record_payload(item) for item in records]


@router.get("/{record_id}/download")
def download_record(
    record_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    record = db.get(MedicalRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    if not _can_see_patient(user, record.patient_id, db):
        raise HTTPException(status_code=403, detail="Not allowed to download this record")
    return FileResponse(record.stored_path, filename=record.original_name)
