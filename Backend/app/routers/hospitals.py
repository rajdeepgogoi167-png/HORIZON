from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.jsonutil import hospital_payload
from app.models import Hospital, Referral, User
from app.schemas import ReferralCreate, ReferralStatus

router = APIRouter(tags=["hospitals"])


@router.get("/hospitals")
def list_hospitals(city: str | None = None, db: Session = Depends(get_db)):
    rows = db.query(Hospital).all()
    out = [hospital_payload(h) for h in rows]
    if city:
        out = [h for h in out if h["city"] == city]
    return out


@router.post("/referrals")
def create_referral(payload: ReferralCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    hospital = None
    if payload.hospital_id:
        hospital = db.get(Hospital, payload.hospital_id)
    elif user.hospital_id:
        hospital = db.get(Hospital, user.hospital_id)
    else:
        hospital = db.query(Hospital).first()
    referral = Referral(
        hospital_id=hospital.id if hospital else None,
        appointment_id=payload.appointment_id,
        from_text=payload.from_text or user.name,
        patient_name=payload.patient_name or user.name,
        note=payload.note,
        urgency=payload.urgency,
        location=payload.location or user.location,
        status="new",
    )
    db.add(referral)
    db.commit()
    db.refresh(referral)
    return {
        "id": referral.id,
        "from": referral.from_text,
        "p": referral.patient_name,
        "note": referral.note,
        "u": referral.urgency,
        "loc": referral.location,
        "st": referral.status,
        "a": referral.ambulance,
        "aid": referral.appointment_id,
        "hospital": hospital.name if hospital else "",
    }


@router.get("/referrals")
def list_referrals(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Referral)
    if user.role == "hospital" and user.hospital_id:
        query = query.filter(Referral.hospital_id == user.hospital_id)
    elif user.role == "patient":
        query = query.filter(Referral.patient_name == user.name)
    rows = query.order_by(Referral.id.desc()).all()
    return [
        {
            "id": r.id,
            "from": r.from_text,
            "p": r.patient_name,
            "note": r.note,
            "u": r.urgency,
            "loc": r.location,
            "st": r.status,
            "a": r.ambulance,
            "aid": r.appointment_id,
        }
        for r in rows
    ]


@router.patch("/referrals/{referral_id}")
def update_referral(
    referral_id: int,
    payload: ReferralStatus,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    referral = db.get(Referral, referral_id)
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")
    if payload.status:
        referral.status = payload.status
    if payload.ambulance:
        referral.ambulance = payload.ambulance
    if payload.status == "accepted" and not referral.ambulance and payload.ambulance is None:
        pass
    db.commit()
    db.refresh(referral)
    return {
        "id": referral.id,
        "st": referral.status,
        "a": referral.ambulance,
        "p": referral.patient_name,
        "from": referral.from_text,
        "note": referral.note,
        "u": referral.urgency,
        "loc": referral.location,
        "aid": referral.appointment_id,
    }
