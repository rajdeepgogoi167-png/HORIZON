from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import BloodNote, BloodRequest, BloodResponse, Donor, Hospital, User
from app.schemas import BloodRequestCreate, DonorUpdate

router = APIRouter(prefix="/blood", tags=["blood"])

COMPATIBLE = {
    "O-": ["O-"],
    "O+": ["O+", "O-"],
    "A-": ["A-", "O-"],
    "A+": ["A+", "A-", "O+", "O-"],
    "B-": ["B-", "O-"],
    "B+": ["B+", "B-", "O+", "O-"],
    "AB-": ["AB-", "A-", "B-", "O-"],
    "AB+": ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"],
}


@router.get("/donor")
def get_donor(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    donor = db.query(Donor).filter(Donor.user_id == user.id).first()
    if not donor:
        return {"on": False, "g": "O+", "mail": ""}
    return {"on": bool(donor.active), "g": donor.blood_group, "mail": donor.email}


@router.post("/donor")
def upsert_donor(payload: DonorUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    donor = db.query(Donor).filter(Donor.user_id == user.id).first()
    if not donor:
        donor = Donor(user_id=user.id, blood_group=payload.blood_group, email=payload.email, active=int(payload.active))
        db.add(donor)
    else:
        donor.blood_group = payload.blood_group
        donor.email = payload.email
        donor.active = int(payload.active)
    db.commit()
    return {"on": bool(donor.active), "g": donor.blood_group, "mail": donor.email}


@router.post("/requests")
def post_request(payload: BloodRequestCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != "hospital":
        raise HTTPException(status_code=403, detail="Only hospitals can post blood requests")
    hospital = db.get(Hospital, user.hospital_id) if user.hospital_id else None
    request = BloodRequest(
        hospital_id=user.hospital_id or 0,
        hospital_name=hospital.name if hospital else user.name,
        blood_group=payload.blood_group,
        units=payload.units,
        urgency=payload.urgency,
        city=payload.city,
    )
    db.add(request)
    db.flush()
    needed = COMPATIBLE.get(payload.blood_group, [payload.blood_group])
    donors = db.query(Donor).filter(Donor.active == 1, Donor.blood_group.in_(needed)).all()
    request.notified = len(donors)
    for donor in donors:
        db.add(
            BloodNote(
                request_id=request.id,
                user_id=donor.user_id,
                blood_group=payload.blood_group,
                units=payload.units,
                urgency=payload.urgency,
                city=payload.city,
                hospital_name=request.hospital_name,
            )
        )
    db.commit()
    db.refresh(request)
    return _request_payload(request, db)


@router.get("/requests")
def list_requests(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(BloodRequest)
    if user.role == "hospital" and user.hospital_id:
        query = query.filter(BloodRequest.hospital_id == user.hospital_id)
    rows = query.order_by(BloodRequest.id.desc()).all()
    return [_request_payload(item, db) for item in rows]


@router.get("/notes")
def list_notes(
    peek: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    notes = db.query(BloodNote).filter(BloodNote.user_id == user.id).order_by(BloodNote.id.desc()).all()
    unread = sum(1 for n in notes if not n.seen)
    payload = [
        {
            "id": n.id,
            "g": n.blood_group,
            "n": n.units,
            "u": n.urgency,
            "c": n.city,
            "h": n.hospital_name,
            "ok": bool(n.accepted),
            "seen": bool(n.seen),
        }
        for n in notes
    ]
    if not peek:
        for note in notes:
            note.seen = 1
        db.commit()
    return {"unread": unread, "notes": payload}


@router.post("/notes/{note_id}/accept")
def accept_note(note_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    note = db.get(BloodNote, note_id)
    if not note or note.user_id != user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    note.accepted = 1
    donor = db.query(Donor).filter(Donor.user_id == user.id).first()
    db.add(
        BloodResponse(
            request_id=note.request_id,
            donor_group=donor.blood_group if donor else note.blood_group,
            eta="~25 min",
        )
    )
    db.commit()
    return {"ok": True}


def _request_payload(item: BloodRequest, db: Session) -> dict:
    responses = db.query(BloodResponse).filter(BloodResponse.request_id == item.id).all()
    return {
        "id": item.id,
        "g": item.blood_group,
        "n": item.units,
        "u": item.urgency,
        "k": item.notified,
        "res": [{"g": r.donor_group, "eta": r.eta} for r in responses],
        "h": item.hospital_name,
        "c": item.city,
    }
