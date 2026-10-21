import json
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Consultation, SignalingEvent, User
from app.schemas import SignalPayload

router = APIRouter(tags=["signaling"])
rooms: dict[int, list[WebSocket]] = defaultdict(list)


@router.post("/signaling")
def store_signal(
    payload: SignalPayload,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """HTTP fallback for WebRTC offer/answer/ICE when a WebSocket cannot stay open."""
    if not db.get(Consultation, payload.consultation_id):
        raise HTTPException(status_code=404, detail="Consultation not found")
    event = SignalingEvent(
        consultation_id=payload.consultation_id,
        event_type=payload.event_type,
        payload=payload.payload,
    )
    db.add(event)
    db.commit()
    return {"stored": True, "id": event.id}


@router.get("/signaling/{consultation_id}")
def list_signals(
    consultation_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    if not db.get(Consultation, consultation_id):
        raise HTTPException(status_code=404, detail="Consultation not found")
    events = (
        db.query(SignalingEvent)
        .filter(SignalingEvent.consultation_id == consultation_id)
        .order_by(SignalingEvent.id.asc())
        .all()
    )
    return [
        {"id": item.id, "event_type": item.event_type, "payload": item.payload}
        for item in events
    ]


@router.websocket("/ws/consultations/{consultation_id}")
async def consultation_socket(websocket: WebSocket, consultation_id: int):
    await websocket.accept()
    rooms[consultation_id].append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            for peer in list(rooms[consultation_id]):
                if peer is websocket:
                    continue
                try:
                    await peer.send_text(data)
                except Exception:
                    rooms[consultation_id].remove(peer)
    except WebSocketDisconnect:
        if websocket in rooms[consultation_id]:
            rooms[consultation_id].remove(websocket)
        for peer in list(rooms[consultation_id]):
            try:
                await peer.send_text(json.dumps({"type": "peer_left"}))
            except Exception:
                pass
