# FitQuest AI — Render Production Build (Fixed)

FitQuest AI is a Streamlit fitness application with:

- PostgreSQL-backed authentication and user progress
- Persistent login sessions
- MediaPipe pose detection
- WebRTC live camera workouts
- Rep counting and form scoring
- XP, levels, streaks, challenges and leaderboard

## 1. Database

Local development uses SQLite automatically.

Render production uses PostgreSQL automatically whenever `DATABASE_URL` is present.

For the existing Render deployment, `DATABASE_URL` should point to the **Internal Database URL** of the `fitquest-db` PostgreSQL service.

Do not commit database credentials to GitHub.

## 2. Local run

```powershell
.venv\Scripts\activate
python -m pip install -r requirements.txt
streamlit run main.py
```

## 3. Render

The web service starts with:

```text
streamlit run main.py --server.address 0.0.0.0 --server.port $PORT
```

Required environment variable:

```text
DATABASE_URL=<Render PostgreSQL Internal Database URL>
```

Optional but recommended for restrictive networks:

```text
CLOUDFLARE_TURN_KEY_ID=<your Cloudflare TURN key ID>
CLOUDFLARE_TURN_API_TOKEN=<your Cloudflare API token>
```

## 4. Authentication behavior

The fixed build creates the account in the active production database, reads it back immediately, starts a persistent session, and validates the session against the same database on subsequent page loads.

If an account was created in an older local SQLite database before PostgreSQL was connected, it will not automatically exist in Render PostgreSQL. Create a new test account on the live Render deployment.

## 5. Camera behavior

The fixed build uses `streamlit-webrtc` 0.49.4, multiple STUN endpoints, a lower default camera resolution/frame rate, and proper processor cleanup. Remote webcam access requires HTTPS and WebRTC ICE connectivity.

If camera connection still fails only on a restrictive network, configure Cloudflare TURN using the two Render environment variables above.

See:

- `DATABASE_TROUBLESHOOTING.md`
- `CAMERA_TROUBLESHOOTING.md`
