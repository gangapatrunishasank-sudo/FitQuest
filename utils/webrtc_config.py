"""WebRTC ICE server configuration for FitQuest AI.

STUN is included by default. In production, Cloudflare TURN can be enabled
with short-lived credentials generated server-side from two Render secrets:

    CLOUDFLARE_TURN_KEY_ID
    CLOUDFLARE_TURN_API_TOKEN

The long-lived Cloudflare API token never reaches the browser.
"""

import os
from typing import Any

import requests


CLOUDFLARE_TURN_ENDPOINT = (
    "https://rtc.live.cloudflare.com/v1/turn/keys/{key_id}/"
    "credentials/generate-ice-servers"
)


def get_ice_servers() -> list[dict[str, Any]]:
    """Return browser ICE servers, including short-lived TURN credentials.

    The app always has public STUN servers. If Cloudflare TURN secrets are
    configured, the server requests temporary TURN credentials and appends
    the returned ICE servers. Failure to obtain TURN does not crash the app;
    STUN remains available and the caller can show a useful diagnostic.
    """

    # Multiple public STUN endpoints improve connectivity when one provider
    # is blocked or slow. TURN can be appended below when Render secrets are
    # configured.
    ice_servers: list[dict[str, Any]] = [
        {"urls": [
            "stun:stun.l.google.com:19302",
            "stun:stun1.l.google.com:19302",
        ]},
        {"urls": [
            "stun:stun.cloudflare.com:3478",
            "stun:stun.cloudflare.com:53",
        ]},
    ]

    key_id = os.getenv("CLOUDFLARE_TURN_KEY_ID", "").strip()
    api_token = os.getenv("CLOUDFLARE_TURN_API_TOKEN", "").strip()

    if not key_id or not api_token:
        return ice_servers

    try:
        response = requests.post(
            CLOUDFLARE_TURN_ENDPOINT.format(key_id=key_id),
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
            },
            json={"ttl": 3600},
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        generated = payload.get("iceServers", [])
        if isinstance(generated, list):
            ice_servers.extend(generated)
    except Exception:
        # Never expose the API token or the raw provider error to the browser.
        # STUN remains usable when TURN is temporarily unavailable.
        pass

    return ice_servers


def turn_is_configured() -> bool:
    return bool(
        os.getenv("CLOUDFLARE_TURN_KEY_ID", "").strip()
        and os.getenv("CLOUDFLARE_TURN_API_TOKEN", "").strip()
    )
