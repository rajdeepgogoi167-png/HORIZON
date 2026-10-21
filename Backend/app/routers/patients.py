from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Patient, User
from app.schemas import PatientCreate, PatientOut

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("", response_model=PatientOut)
def add_patient(
    payload: PatientCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    patient = Patient(
        name=payload.name,
        age=payload.age,
        village=payload.village,
        gender=payload.gender,
        city=payload.city,
        blood_group=payload.blood_group,
        emergency_contact=payload.emergency_contact,
        phone=payload.phone,
        location=payload.location,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("", response_model=list[PatientOut])
def list_patients(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role == "patient" and user.patient_id:
        row = db.get(Patient, user.patient_id)
        return [row] if row else []
    return db.query(Patient).all()


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if user.role == "patient" and user.patient_id != patient_id:
        raise HTTPException(status_code=403, detail="Not your patient record")
    return patient
