from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.adaptive import decide_quality
from app.database import get_db
from app.deps import get_current_user
from app.jsonutil import consultation_payload, dumps
from app.models import Consultation, Doctor, Message, NetworkReport, Patient, User
from app.schemas import (
    ConsultationCreate,
    MessageCreate,
    MessageOut,
    NotesUpdate,
    RatingUpdate,
    StatusUpdate,
)

router = APIRouter(prefix="/consultations", tags=["consultations"])


def _require(consultation: Consultation | None) -> Consultation:
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    return consultation


@router.post("")
def create_consultation(
    payload: ConsultationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doctor = db.get(Doctor, payload.doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    patient_id = payload.patient_id or user.patient_id
    if user.role == "patient" and user.patient_id:
        patient_id = user.patient_id
    patient = db.get(Patient, patient_id) if patient_id else None
    if not patient:
        raise HTTPException(status_code=400, detail="Complete patient onboarding first")

    decision = decide_quality(payload.bandwidth_kbps, payload.latency_ms, payload.packet_loss)
    consultation = Consultation(
        doctor_id=doctor.id,
        patient_id=patient.id,
        doctor_name=doctor.name,
        patient_name=patient.name,
        symptoms=payload.symptoms,
        status="new",
        mode=decision.mode,
        quality_profile=decision.quality_profile,
        consult_type=payload.consult_type,
        slot_time=payload.slot_time,
        files_json=dumps(payload.files),
    )
    db.add(consultation)
    db.flush()
    db.add(
        NetworkReport(
            consultation_id=consultation.id,
            bandwidth_kbps=payload.bandwidth_kbps,
            latency_ms=payload.latency_ms,
            packet_loss=payload.packet_loss,
            recommended_mode=decision.mode,
            recommended_profile=decision.quality_profile,
        )
    )
    db.commit()
    db.refresh(consultation)
    return consultation_payload(consultation)


@router.get("")
def list_consultations(status: str | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Consultation)
    if user.role == "patient" and user.patient_id:
        query = query.filter(Consultation.patient_id == user.patient_id)
    elif user.role == "doctor" and user.doctor_id:
        query = query.filter(Consultation.doctor_id == user.doctor_id)
    if status:
        query = query.filter(Consultation.status == status)
    rows = query.order_by(Consultation.id.desc()).all()
    return [consultation_payload(item) for item in rows]


@router.get("/{consultation_id}")
def get_consultation(consultation_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = _require(db.get(Consultation, consultation_id))
    if user.role == "patient" and item.patient_id != user.patient_id:
        raise HTTPException(status_code=403, detail="Not your consultation")
    if user.role == "doctor" and item.doctor_id != user.doctor_id:
        raise HTTPException(status_code=403, detail="Not your consultation")
    return consultation_payload(item)


@router.patch("/{consultation_id}")
def update_consultation(
    consultation_id: int,
    payload: StatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = _require(db.get(Consultation, consultation_id))
    if user.role == "patient" and item.patient_id != user.patient_id:
        raise HTTPException(status_code=403, detail="Not your consultation")
    if user.role == "doctor" and item.doctor_id != user.doctor_id:
        raise HTTPException(status_code=403, detail="Not your consultation")
    allowed = {"new", "accepted", "cancelled", "live", "completed"}
    if payload.status not in allowed:
        raise HTTPException(status_code=400, detail="Unknown consultation status")
    item.status = payload.status
    if payload.notes is not None:
        item.notes = payload.notes
    db.commit()
    db.refresh(item)
    return consultation_payload(item)


@router.post("/{consultation_id}/notes")
def add_notes(consultation_id: int, payload: NotesUpdate, db: Session = Depends(get_db)):
    consultation = _require(db.get(Consultation, consultation_id))
    consultation.notes = payload.notes
    consultation.status = payload.status
    db.commit()
    db.refresh(consultation)
    return consultation_payload(consultation)


@router.post("/{consultation_id}/rate")
def rate_consultation(
    consultation_id: int,
    payload: RatingUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = _require(db.get(Consultation, consultation_id))
    item.rating = payload.rating
    item.status = "completed"
    doctor = db.get(Doctor, item.doctor_id)
    if doctor:
        total = doctor.rating * doctor.review_count + payload.rating
        doctor.review_count += 1
        doctor.rating = round(total / doctor.review_count, 2)
    db.commit()
    db.refresh(item)
    return consultation_payload(item)


@router.post("/{consultation_id}/messages", response_model=MessageOut)
def queue_message(
    consultation_id: int,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _require(db.get(Consultation, consultation_id))
    message = Message(
        consultation_id=consultation_id,
        sender_role=payload.sender_role or user.role,
        sender_id=payload.sender_id or user.id,
        body=payload.body,
        delivered=0,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


@router.get("/{consultation_id}/messages", response_model=list[MessageOut])
def list_messages(
    consultation_id: int,
    pending_only: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _require(db.get(Consultation, consultation_id))
    query = db.query(Message).filter(Message.consultation_id == consultation_id)
    if pending_only:
        query = query.filter(Message.delivered == 0)
    return query.order_by(Message.id.asc()).all()


@router.post("/{consultation_id}/messages/sync", response_model=list[MessageOut])
def sync_messages(consultation_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _require(db.get(Consultation, consultation_id))
    pending = (
        db.query(Message)
        .filter(Message.consultation_id == consultation_id, Message.delivered == 0)
        .all()
    )
    for message in pending:
        message.delivered = 1
    db.commit()
    return pending
