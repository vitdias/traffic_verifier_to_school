from __future__ import annotations

from traffic_alerts.http_client import http_post_json

VOICE_MONKEY_URL = "https://api.voicemonkey.io/trigger"


def _trigger_voicemonkey(token: str, payload: dict) -> None:
    http_post_json(
        VOICE_MONKEY_URL,
        payload=payload,
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )


def set_alexa_volume(token: str, device_id: str, volume: int) -> None:
    payload = {
        "device": device_id,
        "command": "setVolume",
        "value": volume,
    }
    _trigger_voicemonkey(token, payload)


def speak_on_alexa(token: str, device_id: str, text: str) -> None:
    payload = {
        "device": device_id,
        "command": "speak",
        "text": text,
    }
    _trigger_voicemonkey(token, payload)
