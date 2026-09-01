# FitQuest AI — Camera/WebRTC Fix

The AI Workout page uses `streamlit-webrtc` with MediaPipe Pose. Remote camera access requires HTTPS and WebRTC ICE connectivity.

## Changes in this build

- Upgraded `streamlit-webrtc` from 0.47.9 to 0.49.4.
- Uses multiple public STUN endpoints.
- Uses a lower default camera resolution and frame rate to reduce CPU/network pressure on Render Free.
- Keeps optional Cloudflare TURN support.
- Properly releases the MediaPipe processor when the WebRTC session ends.

`streamlit-webrtc` documents that remote deployments need HTTPS and STUN/TURN connectivity, and its examples use `SENDRECV` for processed video. citeturn1search1turn0search7

## If the camera still fails on a restrictive network

Add these Render environment variables:

- `CLOUDFLARE_TURN_KEY_ID`
- `CLOUDFLARE_TURN_API_TOKEN`

The application requests short-lived TURN credentials server-side. The long-lived API token is never sent to the browser.

Do not commit either secret to GitHub.

## Browser test

On the live HTTPS site:

1. Open **AI Workout**.
2. Click **START**.
3. Choose **Allow** for camera permission.
4. Stand side-on with shoulder, elbow and wrist visible.
5. Wait for **Camera connection is active**.
