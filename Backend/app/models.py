from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    role: Mapped[str] = mapped_column(String(20), index=True)
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(20), index=True)
    location: Mapped[str] = mapped_column(String(80), default="")
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    profile_json: Mapped[str] = mapped_column(Text, default="{}")
    approved: Mapped[int] = mapped_column(Integer, default=1)
    doctor_id: Mapped[int | None] = mapped_column(ForeignKey("doctors.id"), nullable=True)
    patient_id: Mapped[int | None] = mapped_column(ForeignKey("patients.id"), nullable=True)
    hospital_id: Mapped[int | None] = mapped_column(ForeignKey("hospitals.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    specialty: Mapped[str] = mapped_column(String(120), default="General")
    available: Mapped[int] = mapped_column(Integer, default=1)
    qualification: Mapped[str] = mapped_column(String(160), default="")
    institution: Mapped[str] = mapped_column(String(160), default="")
    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    fee: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(Float, default=4.8)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    city: Mapped[str] = mapped_column(String(80), default="")
    languages: Mapped[str] = mapped_column(Text, default="[]")
    slots: Mapped[str] = mapped_column(Text, default="[]")
    modes: Mapped[str] = mapped_column(Text, default="[]")
    bio: Mapped[str] = mapped_column(Text, default="")
    keywords: Mapped[str] = mapped_column(Text, default="[]")
    clinic_count: Mapped[int] = mapped_column(Integer, default=1)
    approved: Mapped[int] = mapped_column(Integer, default=1)
    phone: Mapped[str] = mapped_column(String(20), default="")

    consultations = relationship("Consultation", back_populates="doctor")


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    age: Mapped[int] = mapped_column(Integer, default=0)
    village: Mapped[str] = mapped_column(String(120), default="")
    gender: Mapped[str] = mapped_column(String(20), default="")
    city: Mapped[str] = mapped_column(String(80), default="")
    blood_group: Mapped[str] = mapped_column(String(16), default="")
    emergency_contact: Mapped[str] = mapped_column(String(20), default="")
    phone: Mapped[str] = mapped_column(String(20), default="")
    location: Mapped[str] = mapped_column(String(80), default="")

    consultations = relationship("Consultation", back_populates="patient")
    records = relationship("MedicalRecord", back_populates="patient")


class Hospital(Base):
    __tablename__ = "hospitals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    city: Mapped[str] = mapped_column(String(80), default="")
    specialties: Mapped[str] = mapped_column(Text, default="[]")
    registration: Mapped[str] = mapped_column(String(80), default="")
    address: Mapped[str] = mapped_column(String(255), default="")
    desk_phone: Mapped[str] = mapped_column(String(20), default="")


class Consultation(Base):
    __tablename__ = "consultations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"))
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    doctor_name: Mapped[str] = mapped_column(String(120), default="")
    patient_name: Mapped[str] = mapped_column(String(120), default="")
    symptoms: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="new")
    mode: Mapped[str] = mapped_column(String(40), default="store_and_forward")
    quality_profile: Mapped[str] = mapped_column(String(40), default="ultra_low")
    consult_type: Mapped[str] = mapped_column(String(40), default="Video")
    slot_time: Mapped[str] = mapped_column(String(20), default="")
    files_json: Mapped[str] = mapped_column(Text, default="[]")
    notes: Mapped[str] = mapped_column(Text, default="")
    rating: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    doctor = relationship("Doctor", back_populates="consultations")
    patient = relationship("Patient", back_populates="consultations")
    messages = relationship("Message", back_populates="consultation")


class NetworkReport(Base):
    __tablename__ = "network_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    consultation_id: Mapped[int] = mapped_column(ForeignKey("consultations.id"))
    bandwidth_kbps: Mapped[float] = mapped_column(Float)
    latency_ms: Mapped[float] = mapped_column(Float)
    packet_loss: Mapped[float] = mapped_column(Float, default=0.0)
    recommended_mode: Mapped[str] = mapped_column(String(40))
    recommended_profile: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    consultation_id: Mapped[int | None] = mapped_column(ForeignKey("consultations.id"), nullable=True)
    original_name: Mapped[str] = mapped_column(String(255))
    stored_path: Mapped[str] = mapped_column(String(500))
    mime_type: Mapped[str] = mapped_column(String(80), default="application/octet-stream")
    original_bytes: Mapped[int] = mapped_column(Integer, default=0)
    compressed_bytes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="records")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    consultation_id: Mapped[int] = mapped_column(ForeignKey("consultations.id"))
    sender_role: Mapped[str] = mapped_column(String(20))
    sender_id: Mapped[int] = mapped_column(Integer)
    body: Mapped[str] = mapped_column(Text)
    delivered: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    consultation = relationship("Consultation", back_populates="messages")


class SignalingEvent(Base):
    __tablename__ = "signaling_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    consultation_id: Mapped[int] = mapped_column(ForeignKey("consultations.id"))
    event_type: Mapped[str] = mapped_column(String(40))
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hospital_id: Mapped[int | None] = mapped_column(ForeignKey("hospitals.id"), nullable=True)
    appointment_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    from_text: Mapped[str] = mapped_column(String(160), default="")
    patient_name: Mapped[str] = mapped_column(String(120), default="")
    note: Mapped[str] = mapped_column(Text, default="")
    urgency: Mapped[str] = mapped_column(String(40), default="Urgent")
    location: Mapped[str] = mapped_column(String(120), default="")
    status: Mapped[str] = mapped_column(String(40), default="new")
    ambulance: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Donor(Base):
    __tablename__ = "donors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    blood_group: Mapped[str] = mapped_column(String(8))
    email: Mapped[str] = mapped_column(String(160), default="")
    active: Mapped[int] = mapped_column(Integer, default=1)


class BloodRequest(Base):
    __tablename__ = "blood_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hospital_id: Mapped[int] = mapped_column(ForeignKey("hospitals.id"))
    hospital_name: Mapped[str] = mapped_column(String(160), default="")
    blood_group: Mapped[str] = mapped_column(String(8))
    units: Mapped[int] = mapped_column(Integer, default=1)
    urgency: Mapped[str] = mapped_column(String(40), default="Critical")
    city: Mapped[str] = mapped_column(String(80), default="")
    notified: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BloodNote(Base):
    __tablename__ = "blood_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("blood_requests.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    blood_group: Mapped[str] = mapped_column(String(8))
    units: Mapped[int] = mapped_column(Integer, default=1)
    urgency: Mapped[str] = mapped_column(String(40), default="")
    city: Mapped[str] = mapped_column(String(80), default="")
    hospital_name: Mapped[str] = mapped_column(String(160), default="")
    seen: Mapped[int] = mapped_column(Integer, default=0)
    accepted: Mapped[int] = mapped_column(Integer, default=0)


class BloodResponse(Base):
    __tablename__ = "blood_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("blood_requests.id"))
    donor_group: Mapped[str] = mapped_column(String(8))
    eta: Mapped[str] = mapped_column(String(40), default="~25 min")


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    patient_name: Mapped[str] = mapped_column(String(120), default="")
    kind: Mapped[str] = mapped_column(String(40))
    details: Mapped[str] = mapped_column(Text, default="")
    total: Mapped[str] = mapped_column(String(40), default="")
    status: Mapped[str] = mapped_column(String(40), default="requested")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    patient_name: Mapped[str] = mapped_column(String(120), default="")
    specialty: Mapped[str] = mapped_column(String(80))
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="waiting")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
