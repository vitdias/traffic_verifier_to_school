from datetime import datetime, timezone

from traffic_alerts.config import AlertConfig
from traffic_alerts.logic import evaluate_alert


def make_alert(**overrides):
    base = dict(
        label="Teste",
        destination="Escola Morumbi Alphaville",
        latest_arrival_time="18:30",
        notify_buffer_minutes=5,
        schedule_days=["MON", "TUE", "WED", "THU", "FRI"],
        active_window_start="17:00",
        active_window_end="18:30",
        poll_seconds=60,
        channels=["telegram"],
        timezone="America/Sao_Paulo",
        max_notifications_per_day=1,
        message_template="[{label}] ETA {eta_minutes}",
    )
    base.update(overrides)
    return AlertConfig(**base)


def test_slack_above_buffer_should_not_notify():
    alert = make_alert()
    now_utc = datetime(2026, 2, 23, 20, 0, tzinfo=timezone.utc)  # 17:00 Sao Paulo
    # deadline 18:30 local. remaining 90 min. eta 80 min => slack 10 (> 5)
    result = evaluate_alert(alert, now_utc, eta_seconds=80 * 60)

    assert result.should_evaluate is True
    assert result.should_notify is False
    assert result.slack_minutes == 10


def test_slack_within_buffer_should_notify():
    alert = make_alert()
    now_utc = datetime(2026, 2, 23, 20, 0, tzinfo=timezone.utc)  # 17:00 Sao Paulo
    # slack 5 => should notify
    result = evaluate_alert(alert, now_utc, eta_seconds=85 * 60)

    assert result.should_evaluate is True
    assert result.should_notify is True
    assert result.slack_minutes == 5


def test_late_mode_after_deadline_should_notify():
    alert = make_alert(active_window_end="23:59")
    now_utc = datetime(2026, 2, 23, 22, 0, tzinfo=timezone.utc)  # 19:00 Sao Paulo
    result = evaluate_alert(alert, now_utc, eta_seconds=30 * 60)

    assert result.should_notify is True
    assert result.late_mode is True
