from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.jsonutil import doctor_payload, dumps
from app.models import Doctor, User
from app.schemas import DoctorCreate, DoctorOut

router = APIRouter(prefix="/doctors", tags=["doctors"])


@router.post("", response_model=DoctorOut)
def add_doctor(
    payload: DoctorCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role not in {"hospital", "doctor"}:
        raise HTTPException(status_code=403, detail="Only clinicians and hospitals can add doctors")
    doctor = Doctor(
        name=payload.name,
        specialty=payload.specialty,
        qualification=payload.qualification,
        institution=payload.institution,
        experience_years=payload.experience_years,
        fee=payload.fee,
        city=payload.city,
        bio=payload.bio,
        languages=dumps(payload.languages),
        slots=dumps(payload.slots or ["10:00", "16:00"]),
        modes=dumps(payload.modes or ["Video"]),
        keywords=dumps(payload.keywords),
        approved=1,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor_payload(doctor)


@router.get("")
def list_doctors(
    city: str | None = None,
    specialty: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    rows = db.query(Doctor).filter(Doctor.approved == 1).all()
    out = [doctor_payload(d) for d in rows]
    if city:
        out = [d for d in out if d["city"] == city]
    if specialty:
        out = [d for d in out if d["specialty"] == specialty]
    if q:
        needle = q.lower()
        out = [
            d
            for d in out
            if needle in (d["name"] + d["specialty"] + " ".join(d["keywords"])).lower()
        ]
    return out


@router.get("/{doctor_id}")
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor_payload(doctor)
