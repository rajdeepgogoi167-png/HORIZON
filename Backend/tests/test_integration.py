from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_and_catalog():
    assert client.get("/health").json()["ok"] is True
    catalog = client.get("/catalog").json()
    assert catalog["doctors"]
    assert catalog["hospitals"]
    assert catalog["labs"]


def test_patient_consult_and_referral_flow():
    login = client.post(
        "/auth/login",
        json={"role": "patient", "name": "Ravi Kumar", "phone": "9876543210", "location": "26.1, 91.7"},
    )
    assert login.status_code == 200
    token = login.json()["token"]
    headers = {"X-Session-Token": token}

    me = client.post(
        "/auth/onboard",
        headers=headers,
        json={
            "profile": {
                "age": "34",
                "gender": "Male",
                "city": "Guwahati",
                "blood": "O+",
                "ec": "9876543211",
            }
        },
    )
    assert me.status_code == 200
    assert me.json()["patient_id"]

    doctor_id = client.get("/catalog").json()["doctors"][0]["id"]
    booked = client.post(
        "/consultations",
        headers=headers,
        json={
            "doctor_id": doctor_id,
            "symptoms": "Fever for 3 days",
            "consult_type": "Video",
            "slot_time": "10:00",
            "bandwidth_kbps": 400,
            "latency_ms": 120,
            "packet_loss": 0.01,
        },
    )
    assert booked.status_code == 200
    consult = booked.json()
    assert consult["status"] == "new"
    assert consult["doctor_id"] == doctor_id

    notes = client.get("/consultations").json() if False else client.get("/consultations", headers=headers).json()
    assert any(row["id"] == consult["id"] for row in notes)

    referral = client.post(
        "/referrals",
        headers=headers,
        json={
            "from_text": "Patient emergency button",
            "patient_name": "Ravi Kumar",
            "note": "Self-reported emergency.",
            "urgency": "Critical",
            "location": "26.1, 91.7",
        },
    )
    assert referral.status_code == 200
    assert referral.json()["st"] == "new"

    svc = client.post(
        "/services",
        headers=headers,
        json={"kind": "Lab test", "details": "Complete blood count", "total": "₹350"},
    )
    assert svc.status_code == 200
    listed = client.get("/services", headers=headers).json()
    assert listed[0]["k"] == "Lab test"


def test_unauthenticated_patients_hidden():
    assert client.get("/patients").status_code == 401
