from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass
class AlertState:
    notifications_by_day: dict[str, int]


class StateStore:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.state = self._load()

    def _load(self) -> dict[str, AlertState]:
        if not self.file_path.exists():
            return {}
        raw = json.loads(self.file_path.read_text(encoding="utf-8"))
        result: dict[str, AlertState] = {}
        for label, data in raw.items():
            result[label] = AlertState(notifications_by_day=data.get("notifications_by_day", {}))
        return result

    def _save(self) -> None:
        payload = {
            label: {"notifications_by_day": alert_state.notifications_by_day}
            for label, alert_state in self.state.items()
        }
        self.file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def can_notify(self, label: str, day: date, max_notifications_per_day: int) -> bool:
        day_key = day.isoformat()
        alert_state = self.state.get(label, AlertState(notifications_by_day={}))
        return alert_state.notifications_by_day.get(day_key, 0) < max_notifications_per_day

    def mark_notified(self, label: str, day: date) -> None:
        day_key = day.isoformat()
        alert_state = self.state.get(label)
        if alert_state is None:
            alert_state = AlertState(notifications_by_day={})
            self.state[label] = alert_state
        alert_state.notifications_by_day[day_key] = alert_state.notifications_by_day.get(day_key, 0) + 1
        self._save()
