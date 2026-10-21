from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.jsonutil import doctor_payload, hospital_payload
from app.models import Doctor, Hospital
from app.seed import ARTICLES, CITIES, LABS

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("")
def catalog(db: Session = Depends(get_db)):
    doctors = [doctor_payload(d) for d in db.query(Doctor).filter(Doctor.approved == 1).all()]
    hospitals = [hospital_payload(h) for h in db.query(Hospital).all()]
    cities = sorted({*(CITIES), *[d["city"] for d in doctors if d["city"]], *[h["city"] for h in hospitals if h["city"]]})
    specialties = sorted({d["specialty"] for d in doctors})
    return {
        "doctors": doctors,
        "hospitals": hospitals,
        "labs": LABS,
        "articles": ARTICLES,
        "cities": cities,
        "specialties": specialties,
    }
