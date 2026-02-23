from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


VALID_DAYS = {"MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"}
VALID_CHANNELS = {"telegram", "android_notification", "alexa_voice"}


@dataclass(frozen=True)
class EnvConfig:
    google_maps_api_key: str
    telegram_bot_token: str | None
    telegram_chat_id: str | None
    voicemonkey_token: str | None
    voicemonkey_device_id: str | None
    alexa_volume_level: int


@dataclass(frozen=True)
class AlertConfig:
    label: str
    destination: str
    latest_arrival_time: str
    notify_buffer_minutes: int
    schedule_days: list[str]
    active_window_start: str
    active_window_end: str
    poll_seconds: int
    channels: list[str]
    timezone: str
    max_notifications_per_day: int
    message_template: str


@dataclass(frozen=True)
class AppConfig:
    alerts: list[AlertConfig]
    geocode_cache_file: Path
    state_file: Path


def _require_time_format(value: str, field_name: str) -> str:
    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError(f"{field_name} must follow HH:MM format")
    hour, minute = parts
    if not (hour.isdigit() and minute.isdigit()):
        raise ValueError(f"{field_name} must follow HH:MM format")
    h_int = int(hour)
    m_int = int(minute)
    if h_int < 0 or h_int > 23 or m_int < 0 or m_int > 59:
        raise ValueError(f"{field_name} must be a valid 24h time")
    return f"{h_int:02d}:{m_int:02d}"


def load_env(env_file: str = ".env") -> EnvConfig:
    from dotenv import load_dotenv

    load_dotenv(env_file)
    maps_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not maps_key:
        raise ValueError("GOOGLE_MAPS_API_KEY is required")

    volume = int(os.getenv("ALEXA_VOLUME_LEVEL", "6"))
    if volume < 0 or volume > 10:
        raise ValueError("ALEXA_VOLUME_LEVEL must be between 0 and 10")

    return EnvConfig(
        google_maps_api_key=maps_key,
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        voicemonkey_token=os.getenv("VOICEMONKEY_TOKEN"),
        voicemonkey_device_id=os.getenv("VOICEMONKEY_DEVICE_ID"),
        alexa_volume_level=volume,
    )


def _validate_alert(raw_alert: dict[str, Any], default_timezone: str, default_template: str) -> AlertConfig:
    required_fields = [
        "label",
        "destination",
        "latest_arrival_time",
        "notify_buffer_minutes",
        "schedule_days",
        "active_window_start",
        "active_window_end",
        "poll_seconds",
        "channels",
    ]
    for field in required_fields:
        if field not in raw_alert:
            raise ValueError(f"Missing field '{field}' in alert config")

    days = [str(d).upper() for d in raw_alert["schedule_days"]]
    invalid_days = [d for d in days if d not in VALID_DAYS]
    if invalid_days:
        raise ValueError(f"Invalid schedule_days values: {invalid_days}")

    channels = [str(c) for c in raw_alert["channels"]]
    invalid_channels = [c for c in channels if c not in VALID_CHANNELS]
    if invalid_channels:
        raise ValueError(f"Invalid channels values: {invalid_channels}")

    return AlertConfig(
        label=str(raw_alert["label"]),
        destination=str(raw_alert["destination"]),
        latest_arrival_time=_require_time_format(str(raw_alert["latest_arrival_time"]), "latest_arrival_time"),
        notify_buffer_minutes=int(raw_alert["notify_buffer_minutes"]),
        schedule_days=days,
        active_window_start=_require_time_format(str(raw_alert["active_window_start"]), "active_window_start"),
        active_window_end=_require_time_format(str(raw_alert["active_window_end"]), "active_window_end"),
        poll_seconds=int(raw_alert["poll_seconds"]),
        channels=channels,
        timezone=str(raw_alert.get("timezone", default_timezone)),
        max_notifications_per_day=int(raw_alert.get("max_notifications_per_day", 1)),
        message_template=str(raw_alert.get("message_template", default_template)),
    )


def load_app_config(config_file: str = "alerts.yaml") -> AppConfig:
    import yaml

    raw = yaml.safe_load(Path(config_file).read_text(encoding="utf-8")) or {}
    defaults = raw.get("defaults", {})
    default_timezone = str(defaults.get("timezone", "America/Sao_Paulo"))
    default_template = str(
        defaults.get(
            "message_template",
            "[{label}] ETA: {eta_minutes} min | folga: {slack_minutes} min | limite: {latest_arrival_time}",
        )
    )

    raw_alerts = raw.get("alerts", [])
    if not raw_alerts:
        raise ValueError("alerts.yaml must contain at least one alert")

    alerts = [_validate_alert(item, default_timezone, default_template) for item in raw_alerts]
    geocode_cache_file = Path(raw.get("geocode_cache_file", "data/geocode_cache.json"))
    state_file = Path(raw.get("state_file", "data/state.json"))

    return AppConfig(alerts=alerts, geocode_cache_file=geocode_cache_file, state_file=state_file)
