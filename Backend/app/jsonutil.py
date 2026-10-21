import json


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def loads(value, default=None):
    if default is None:
        default = []
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def doctor_payload(doctor) -> dict:
    return {
        "id": doctor.id,
        "name": doctor.name,
        "specialty": doctor.specialty,
        "available": doctor.available,
        "qualification": doctor.qualification,
        "institution": doctor.institution,
        "experience_years": doctor.experience_years,
        "fee": doctor.fee,
        "rating": doctor.rating,
        "review_count": doctor.review_count,
        "city": doctor.city,
        "languages": loads(doctor.languages),
        "slots": loads(doctor.slots),
        "modes": loads(doctor.modes),
        "bio": doctor.bio,
        "keywords": loads(doctor.keywords),
        "clinic_count": doctor.clinic_count,
        "approved": doctor.approved,
    }


def hospital_payload(hospital) -> dict:
    return {
        "id": hospital.id,
        "name": hospital.name,
        "city": hospital.city,
        "specialties": loads(hospital.specialties),
        "registration": hospital.registration,
        "address": hospital.address,
        "desk_phone": hospital.desk_phone,
    }


def consultation_payload(item) -> dict:
    return {
        "id": item.id,
        "doctor_id": item.doctor_id,
        "patient_id": item.patient_id,
        "doctor_name": item.doctor_name,
        "patient_name": item.patient_name,
        "symptoms": item.symptoms,
        "status": item.status,
        "mode": item.mode,
        "quality_profile": item.quality_profile,
        "consult_type": item.consult_type,
        "slot_time": item.slot_time,
        "files": loads(item.files_json),
        "notes": item.notes,
        "rating": item.rating,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }
