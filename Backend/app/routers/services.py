from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Question, ServiceRequest, User
from app.schemas import QuestionCreate, ServiceCreate

router = APIRouter(tags=["services"])


@router.post("/services")
def create_service(payload: ServiceCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not user.patient_id:
        raise HTTPException(status_code=400, detail="Complete patient onboarding first")
    item = ServiceRequest(
        patient_id=user.patient_id,
        patient_name=user.name,
        kind=payload.kind,
        details=payload.details,
        total=payload.total,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {
        "id": item.id,
        "k": item.kind,
        "d": item.details,
        "t": item.total,
        "p": item.patient_name,
        "st": item.status,
    }


@router.get("/services")
def list_services(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(ServiceRequest)
    if user.patient_id:
        query = query.filter(ServiceRequest.patient_id == user.patient_id)
    rows = query.order_by(ServiceRequest.id.desc()).all()
    return [{"id": i.id, "k": i.kind, "d": i.details, "t": i.total, "p": i.patient_name, "st": i.status} for i in rows]


@router.post("/questions")
def create_question(payload: QuestionCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not user.patient_id:
        raise HTTPException(status_code=400, detail="Complete patient onboarding first")
    item = Question(
        patient_id=user.patient_id,
        patient_name=user.name,
        specialty=payload.specialty,
        body=payload.body,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "p": item.patient_name, "s": item.specialty, "t": item.body, "st": item.status}


@router.get("/questions")
def list_questions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Question)
    if user.patient_id:
        query = query.filter(Question.patient_id == user.patient_id)
    rows = query.order_by(Question.id.desc()).all()
    return [{"id": i.id, "p": i.patient_name, "s": i.specialty, "t": i.body, "st": i.status} for i in rows]
