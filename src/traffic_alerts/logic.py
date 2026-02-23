from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from zoneinfo import ZoneInfo

from traffic_alerts.config import AlertConfig

WEEKDAY_MAP = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


@dataclass(frozen=True)
class TriggerEvaluation:
    should_evaluate: bool
    should_notify: bool
    late_mode: bool
    slack_minutes: int
    eta_minutes: int
    reason: str
    deadline: datetime


def parse_hhmm(value: str) -> time:
    hour, minute = value.split(":")
    return time(hour=int(hour), minute=int(minute))


def _is_in_active_window(now: datetime, start_hhmm: str, end_hhmm: str) -> bool:
    start = parse_hhmm(start_hhmm)
    end = parse_hhmm(end_hhmm)
    now_t = now.time().replace(second=0, microsecond=0)
    return start <= now_t <= end


def evaluate_alert(alert: AlertConfig, now_utc: datetime, eta_seconds: int) -> TriggerEvaluation:
    tz = ZoneInfo(alert.timezone)
    now_local = now_utc.astimezone(tz)
    weekday = WEEKDAY_MAP[now_local.weekday()]
    if weekday not in alert.schedule_days:
        deadline = now_local.replace(hour=23, minute=59, second=59, microsecond=0)
        return TriggerEvaluation(False, False, False, 9999, eta_seconds // 60, "weekday_not_scheduled", deadline)

    if not _is_in_active_window(now_local, alert.active_window_start, alert.active_window_end):
        deadline = now_local.replace(hour=23, minute=59, second=59, microsecond=0)
        return TriggerEvaluation(False, False, False, 9999, eta_seconds // 60, "outside_active_window", deadline)

    latest_time = parse_hhmm(alert.latest_arrival_time)
    deadline = now_local.replace(hour=latest_time.hour, minute=latest_time.minute, second=0, microsecond=0)

    slack_seconds = int((deadline - now_local).total_seconds()) - eta_seconds
    slack_minutes = slack_seconds // 60
    eta_minutes = eta_seconds // 60

    if now_local > deadline:
        return TriggerEvaluation(True, True, True, slack_minutes, eta_minutes, "deadline_passed_late_alert", deadline)

    should_notify = slack_minutes <= alert.notify_buffer_minutes
    reason = "slack_within_buffer" if should_notify else "slack_above_buffer"
    return TriggerEvaluation(True, should_notify, False, slack_minutes, eta_minutes, reason, deadline)
