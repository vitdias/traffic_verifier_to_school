from __future__ import annotations

from traffic_alerts.http_client import http_post_json


def send_telegram_message(bot_token: str, chat_id: str, message: str) -> None:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = http_post_json(
        url,
        payload={
            "chat_id": chat_id,
            "text": message,
            "disable_web_page_preview": True,
        },
        timeout=15,
    )
    if not payload.get("ok"):
        raise RuntimeError(f"Telegram API error: {payload}")
