import json
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.jsonutil import dumps, loads
from app.models import Doctor, Hospital, Patient, User
from app.schemas import LoginRequest, OnboardRequest
from app.seed import TAGS

router = APIRouter(prefix="/auth", tags=["auth"])


def _city_from_address(address: str) -> str:
    if not address:
        return ""
    parts = [p.strip() for p in address.replace(",", " ").split() if p.strip()]
    return parts[-1] if parts else ""


def user_payload(user: User, profile: dict | None = None) -> dict:
    if profile is None:
        try:
            profile = json.loads(user.profile_json or "{}")
        except json.JSONDecodeError:
            profile = {}
    return {
        "token": user.token,
        "user_id": user.id,
        "role": user.role,
        "name": user.name,
        "phone": user.phone,
        "location": user.location,
        "approved": bool(user.approved),
        "doctor_id": user.doctor_id,
        "patient_id": user.patient_id,
        "hospital_id": user.hospital_id,
        "profile": profile,
    }


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    role = payload.role.strip().lower()
    if role not in {"patient", "doctor", "hospital"}:
        raise HTTPException(status_code=400, detail="Choose patient, doctor, or hospital.")
    phone = payload.phone.replace(" ", "").replace("-", "")
    if phone.startswith("+91"):
        phone = phone[3:]
    user = db.query(User).filter(User.role == role, User.phone == phone).first()
    if not user:
        user = User(
            role=role,
            name=payload.name.strip(),
            phone=phone,
            location=payload.location,
            token=secrets.token_hex(24),
            profile_json="{}",
            approved=0 if role == "doctor" else 1,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.name = payload.name.strip()
        user.location = payload.location or user.location
        user.token = secrets.token_hex(24)
        db.commit()
        db.refresh(user)
    return user_payload(user)


@router.post("/onboard")
def onboard(payload: OnboardRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    profile = payload.profile or {}
    user.profile_json = dumps(profile)

    if user.role == "patient":
        patient = db.get(Patient, user.patient_id) if user.patient_id else None
        if not patient:
            patient = Patient(name=user.name)
            db.add(patient)
            db.flush()
            user.patient_id = patient.id
        patient.name = user.name
        patient.age = int(profile.get("age") or 0)
        patient.village = profile.get("city") or ""
        patient.city = profile.get("city") or ""
        patient.gender = profile.get("gender") or ""
        patient.blood_group = profile.get("blood") or ""
        patient.emergency_contact = profile.get("ec") or ""
        patient.phone = user.phone
        patient.location = user.location
        user.approved = 1

    elif user.role == "doctor":
        doctor = db.get(Doctor, user.doctor_id) if user.doctor_id else None
        match = (
            db.query(Doctor)
            .filter(Doctor.name.ilike(user.name), Doctor.phone.in_(["", user.phone]))
            .first()
        )
        if not doctor and match and not db.query(User).filter(User.doctor_id == match.id, User.id != user.id).first():
            doctor = match
        if not doctor:
            doctor = Doctor(name=user.name, specialty=profile.get("spec") or "General Medicine", approved=0)
            db.add(doctor)
            db.flush()
        doctor.name = user.name
        doctor.phone = user.phone
        doctor.specialty = profile.get("spec") or doctor.specialty
        doctor.qualification = profile.get("qual") or doctor.qualification
        doctor.institution = profile.get("inst") or doctor.institution
        doctor.experience_years = int(profile.get("exp") or doctor.experience_years or 0)
        doctor.city = profile.get("city") or doctor.city or user.location or ""
        if not loads(doctor.slots):
            doctor.slots = dumps(["10:00", "11:30", "16:00"])
        if not loads(doctor.modes):
            doctor.modes = dumps(["Video", "Audio", "In person"])
        if not loads(doctor.keywords):
            doctor.keywords = dumps(TAGS.get(doctor.specialty, []))
        if not doctor.bio:
            doctor.bio = f"{doctor.specialty} specialist on Horizon."
        if not doctor.fee:
            doctor.fee = 400
        user.doctor_id = doctor.id
        user.approved = doctor.approved

    elif user.role == "hospital":
        hospital = db.get(Hospital, user.hospital_id) if user.hospital_id else None
        name = profile.get("hn") or user.name
        match = db.query(Hospital).filter(Hospital.name.ilike(name)).first()
        if not hospital and match:
            hospital = match
        if not hospital:
            hospital = Hospital(name=name)
            db.add(hospital)
            db.flush()
        hospital.name = name
        hospital.registration = profile.get("reg") or hospital.registration
        hospital.address = profile.get("addr") or hospital.address
        hospital.city = profile.get("city") or hospital.city or _city_from_address(hospital.address)
        hospital.desk_phone = profile.get("desk") or user.phone
        user.hospital_id = hospital.id
        user.name = name
        user.approved = 1

    db.commit()
    db.refresh(user)
    return user_payload(user)


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return user_payload(user)


@router.post("/approve")
def approve_self(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Demo reviewer action: mark the signed-in doctor as verified."""
    if user.role != "doctor":
        raise HTTPException(status_code=400, detail="Only doctor accounts need approval")
    user.approved = 1
    if user.doctor_id:
        doctor = db.get(Doctor, user.doctor_id)
        if doctor:
            doctor.approved = 1
    db.commit()
    return user_payload(user)
