import json
from unittest.mock import Mock, patch

from traffic_alerts.location import get_current_location
from traffic_alerts.routing import GoogleRoutingClient


def test_location_with_mocked_termux_location():
    mocked_run = Mock()
    mocked_run.return_value.stdout = json.dumps({"latitude": -23.55, "longitude": -46.63})

    with patch("subprocess.run", mocked_run):
        coords = get_current_location(max_retries=1)

    assert coords.lat == -23.55
    assert coords.lng == -46.63


def test_routing_with_mocked_google_requests(tmp_path):
    cache_file = tmp_path / "cache.json"
    client = GoogleRoutingClient("fake-key", cache_file)

    geocode_payload = {
        "status": "OK",
        "results": [{"geometry": {"location": {"lat": -23.5, "lng": -46.6}}}],
    }
    directions_payload = {
        "status": "OK",
        "routes": [
            {
                "legs": [
                    {
                        "duration_in_traffic": {"value": 1800},
                        "end_address": "End Mock",
                    }
                ]
            }
        ],
    }

    with patch("traffic_alerts.routing.http_get_json", side_effect=[geocode_payload, directions_payload]):
        eta = client.get_eta_in_traffic(origin=type("C", (), {"lat": -23.4, "lng": -46.5})(), destination="Av Paulista, 1000")

    assert eta.eta_seconds == 1800
    assert eta.destination_label == "End Mock"
