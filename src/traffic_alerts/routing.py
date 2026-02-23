from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

from traffic_alerts.http_client import http_get_json
from traffic_alerts.location import Coordinates


@dataclass(frozen=True)
class ETAResult:
    eta_seconds: int
    destination_label: str


class GoogleRoutingClient:
    def __init__(self, api_key: str, geocode_cache_file: Path) -> None:
        self.api_key = api_key
        self.geocode_cache_file = geocode_cache_file
        self.geocode_cache_file.parent.mkdir(parents=True, exist_ok=True)
        self._cache = self._load_cache()

    def _load_cache(self) -> dict[str, dict[str, float]]:
        if not self.geocode_cache_file.exists():
            return {}
        return json.loads(self.geocode_cache_file.read_text(encoding="utf-8"))

    def _save_cache(self) -> None:
        self.geocode_cache_file.write_text(json.dumps(self._cache, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _is_lat_lng(destination: str) -> bool:
        parts = [p.strip() for p in destination.split(",")]
        if len(parts) != 2:
            return False
        try:
            float(parts[0])
            float(parts[1])
            return True
        except ValueError:
            return False

    def _geocode(self, destination: str, max_retries: int = 3, retry_delay_seconds: int = 2) -> Coordinates:
        if self._is_lat_lng(destination):
            lat, lng = [float(p.strip()) for p in destination.split(",")]
            return Coordinates(lat=lat, lng=lng)

        if destination in self._cache:
            cached = self._cache[destination]
            return Coordinates(lat=float(cached["lat"]), lng=float(cached["lng"]))

        last_error: Exception | None = None
        for attempt in range(1, max_retries + 1):
            try:
                payload = http_get_json(
                    "https://maps.googleapis.com/maps/api/geocode/json",
                    params={"address": destination, "key": self.api_key},
                    timeout=15,
                )
                status = payload.get("status")
                if status != "OK" or not payload.get("results"):
                    raise RuntimeError(f"Geocoding failed with status={status}")
                location = payload["results"][0]["geometry"]["location"]
                coords = Coordinates(lat=float(location["lat"]), lng=float(location["lng"]))
                self._cache[destination] = {"lat": coords.lat, "lng": coords.lng}
                self._save_cache()
                return coords
            except Exception as exc:
                last_error = exc
                if attempt < max_retries:
                    time.sleep(retry_delay_seconds)

        raise RuntimeError(f"Unable to geocode destination '{destination}' after retries: {last_error}")

    def get_eta_in_traffic(
        self,
        origin: Coordinates,
        destination: str,
        max_retries: int = 3,
        retry_delay_seconds: int = 2,
    ) -> ETAResult:
        dest_coords = self._geocode(destination, max_retries=max_retries, retry_delay_seconds=retry_delay_seconds)
        params = {
            "origin": f"{origin.lat},{origin.lng}",
            "destination": f"{dest_coords.lat},{dest_coords.lng}",
            "departure_time": "now",
            "traffic_model": "best_guess",
            "key": self.api_key,
        }

        last_error: Exception | None = None
        for attempt in range(1, max_retries + 1):
            try:
                payload = http_get_json(
                    "https://maps.googleapis.com/maps/api/directions/json",
                    params=params,
                    timeout=20,
                )
                status = payload.get("status")
                if status != "OK" or not payload.get("routes"):
                    raise RuntimeError(f"Directions failed with status={status}")
                leg = payload["routes"][0]["legs"][0]
                duration_traffic = leg.get("duration_in_traffic") or leg.get("duration")
                eta_seconds = int(duration_traffic["value"])
                return ETAResult(eta_seconds=eta_seconds, destination_label=leg.get("end_address", destination))
            except Exception as exc:
                last_error = exc
                if attempt < max_retries:
                    time.sleep(retry_delay_seconds)

        raise RuntimeError(f"Unable to retrieve ETA after retries: {last_error}")
