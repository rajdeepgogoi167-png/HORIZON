# Horizon

Horizon is a telemedicine site for patients, doctors, and hospitals. The browser app in `Frontend/` and the FastAPI service in `Backend/` share one session, one catalog, and live consultation APIs (adaptive quality, compressed records, WebRTC signaling, referrals, and blood requests).

Open the site from the API origin so the UI and backend stay on the same host. No Node install is required.

## Run locally

You need Python 3.11+. From PowerShell:

```powershell
cd d:\HORIZON\Backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Then open:

- App: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

A demo doctor must tap **Reviewer action: approve this doctor** once after onboarding. Seeded specialists (Meera Nair, Arjun Rao, and others) are already verified for patients to book. Sign in with the exact seeded name (for example `Dr. Meera Nair`) to claim that catalog profile.

## Try the full loop

1. Sign in as a **patient**, complete the profile, describe symptoms, and book a video slot.
2. In another browser (or a private window), sign in as a **doctor**, approve the account, accept the request, and start the consultation.
3. Sign in as a **hospital** to see emergency referrals and post blood requests.

Location is required at login because emergency referrals share it with the hospital desk.

## Configuration

See `Backend/.env.example`:

- `DATABASE_URL` — defaults to SQLite `horizon.db` in the Backend folder
- `CORS_ORIGINS` — use `*` locally. Set explicit origins only if you serve `Frontend/index.html` from another host (Live Server, etc.)

If you open the HTML file directly, set `window.HORIZON_API = "http://127.0.0.1:8000"` before `script.js` loads.

Session tokens travel in the `X-Session-Token` header. File downloads also accept `?session_token=`.
