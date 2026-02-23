from __future__ import annotations

import hashlib
import logging

from traffic_alerts.config import AlertConfig, EnvConfig
from traffic_alerts.notify_alexa import set_alexa_volume, speak_on_alexa
from traffic_alerts.notify_android import send_android_notification
from traffic_alerts.notify_telegram import send_telegram_message

logger = logging.getLogger(__name__)


def build_message(alert: AlertConfig, eta_minutes: int, slack_minutes: int) -> str:
    return alert.message_template.format(
        label=alert.label,
        eta_minutes=eta_minutes,
        slack_minutes=slack_minutes,
        latest_arrival_time=alert.latest_arrival_time,
        destination=alert.destination,
        notify_buffer_minutes=alert.notify_buffer_minutes,
    )


def notify_channels(alert: AlertConfig, env: EnvConfig, message: str) -> None:
    for channel in alert.channels:
        try:
            if channel == "telegram":
                if not env.telegram_bot_token or not env.telegram_chat_id:
                    raise RuntimeError("telegram channel configured but TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID missing")
                send_telegram_message(env.telegram_bot_token, env.telegram_chat_id, message)
            elif channel == "android_notification":
                notification_id = int(hashlib.sha256(alert.label.encode("utf-8")).hexdigest()[:8], 16)
                send_android_notification(title=f"Alerta: {alert.label}", content=message, notification_id=notification_id)
            elif channel == "alexa_voice":
                if not env.voicemonkey_token or not env.voicemonkey_device_id:
                    raise RuntimeError("alexa_voice channel configured but VOICEMONKEY_TOKEN/VOICEMONKEY_DEVICE_ID missing")
                try:
                    set_alexa_volume(env.voicemonkey_token, env.voicemonkey_device_id, env.alexa_volume_level)
                except Exception:
                    logger.exception("Falha ao ajustar volume Alexa; tentando enviar fala mesmo assim")
                speak_on_alexa(env.voicemonkey_token, env.voicemonkey_device_id, message)
            else:
                logger.warning("Canal de notificação desconhecido: %s", channel)
        except Exception:
            logger.exception("Erro ao notificar canal %s do alerta %s", channel, alert.label)
