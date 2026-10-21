from datetime import datetime

from pydantic import BaseModel, Field


class DoctorCreate(BaseModel):
    name: str
    specialty: str = "General"
    qualification: str = ""
    institution: str = ""
    experience_years: int = 0
    fee: int = 0
    city: str = ""
    bio: str = ""
    languages: list[str] = []
    slots: list[str] = []
    modes: list[str] = ["Video"]
    keywords: list[str] = []


class DoctorOut(BaseModel):
    id: int
    name: str
    specialty: str
    available: int
    qualification: str = ""
    institution: str = ""
    experience_years: int = 0
    fee: int = 0
    rating: float = 4.8
    review_count: int = 0
    city: str = ""
    languages: list[str] = []
    slots: list[str] = []
    modes: list[str] = []
    bio: str = ""
    keywords: list[str] = []
    clinic_count: int = 1
    approved: int = 1

    class Config:
        from_attributes = True


class PatientCreate(BaseModel):
    name: str
    age: int = 0
    village: str = ""
    gender: str = ""
    city: str = ""
    blood_group: str = ""
    emergency_contact: str = ""
    phone: str = ""
    location: str = ""


class PatientOut(BaseModel):
    id: int
    name: str
    age: int
    village: str
    gender: str = ""
    city: str = ""
    blood_group: str = ""
    emergency_contact: str = ""
    phone: str = ""
    location: str = ""

    class Config:
        from_attributes = True


class ConsultationCreate(BaseModel):
    doctor_id: int
    patient_id: int | None = None
    symptoms: str = ""
    bandwidth_kbps: float = Field(ge=0, default=64)
    latency_ms: float = Field(ge=0, default=400)
    packet_loss: float = Field(ge=0, le=1, default=0.05)
    consult_type: str = "Video"
    slot_time: str = ""
    files: list[str] = []


class ConsultationOut(BaseModel):
    id: int
    doctor_id: int
    patient_id: int
    doctor_name: str = ""
    patient_name: str = ""
    symptoms: str
    status: str
    mode: str
    quality_profile: str
    consult_type: str = "Video"
    slot_time: str = ""
    files: list[str] = []
    notes: str = ""
    rating: int = 0
    created_at: datetime | str | None = None

    class Config:
        from_attributes = True


class StatusUpdate(BaseModel):
    status: str
    notes: str | None = None


class RatingUpdate(BaseModel):
    rating: int = Field(ge=1, le=5)


class NetworkProbe(BaseModel):
    consultation_id: int
    bandwidth_kbps: float
    latency_ms: float
    packet_loss: float = 0.0


class QualityDecision(BaseModel):
    mode: str
    quality_profile: str
    max_video_bitrate_kbps: int
    resolution: str
    fps: int
    audio_bitrate_kbps: int
    use_store_and_forward: bool
    reason: str


class MessageCreate(BaseModel):
    sender_role: str
    sender_id: int | None = None
    body: str


class MessageOut(BaseModel):
    id: int
    consultation_id: int
    sender_role: str
    sender_id: int
    body: str
    delivered: int
    created_at: datetime

    class Config:
        from_attributes = True


class NotesUpdate(BaseModel):
    notes: str
    status: str = "completed"


class SignalPayload(BaseModel):
    consultation_id: int
    event_type: str
    payload: str


class LoginRequest(BaseModel):
    role: str
    name: str
    phone: str
    location: str = ""


class OnboardRequest(BaseModel):
    profile: dict


class ReferralCreate(BaseModel):
    from_text: str = ""
    patient_name: str = ""
    note: str = ""
    urgency: str = "Urgent"
    location: str = ""
    appointment_id: int | None = None
    hospital_id: int | None = None


class ReferralStatus(BaseModel):
    status: str | None = None
    ambulance: str | None = None


class DonorUpdate(BaseModel):
    blood_group: str
    email: str
    active: bool = True


class BloodRequestCreate(BaseModel):
    blood_group: str
    units: int = Field(ge=1, default=1)
    urgency: str = "Critical"
    city: str = "Guwahati"


class ServiceCreate(BaseModel):
    kind: str
    details: str
    total: str = ""


class QuestionCreate(BaseModel):
    specialty: str
    body: str
