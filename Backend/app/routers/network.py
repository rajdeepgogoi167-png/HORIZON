import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.adaptive import decide_quality
from app.database import get_db
from app.deps import get_current_user
from app.models import Consultation, NetworkReport, User
from app.schemas import NetworkProbe, QualityDecision

router = APIRouter(prefix="/network", tags=["network"])


@router.get("/ping")
def ping():
    return {"t": time.time()}


@router.get("/blob")
def speed_blob():
    return Response(content=b"h" * 32_768, media_type="application/octet-stream")


@router.post("/probe", response_model=QualityDecision)
def probe_network(
    payload: NetworkProbe,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    consultation = db.get(Consultation, payload.consultation_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    decision = decide_quality(payload.bandwidth_kbps, payload.latency_ms, payload.packet_loss)
    consultation.mode = decision.mode
    consultation.quality_profile = decision.quality_profile
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
    return decision


@router.get("/profiles", response_model=QualityDecision)
def preview_profile(bandwidth_kbps: float, latency_ms: float = 200, packet_loss: float = 0.0):
    return decide_quality(bandwidth_kbps, latency_ms, packet_loss)
