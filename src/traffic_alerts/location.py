from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class Coordinates:
    lat: float
    lng: float


def get_current_location(max_retries: int = 3, retry_delay_seconds: int = 3) -> Coordinates:
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            result = subprocess.run(
                ["termux-location", "-p", "gps", "-r", "last"],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(result.stdout)
            lat = float(payload["latitude"])
            lng = float(payload["longitude"])
            return Coordinates(lat=lat, lng=lng)
        except Exception as exc:
            last_error = exc
            if attempt < max_retries:
                time.sleep(retry_delay_seconds)

    raise RuntimeError(f"Unable to retrieve GPS location after retries: {last_error}")
