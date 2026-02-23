from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def http_get_json(url: str, params: dict, timeout: int = 20) -> dict:
    query = urlencode(params)
    full_url = f"{url}?{query}"
    req = Request(full_url, method="GET")
    with urlopen(req, timeout=timeout) as resp:
        payload = resp.read().decode("utf-8")
    return json.loads(payload)


def http_post_json(url: str, payload: dict, headers: dict | None = None, timeout: int = 20) -> dict:
    final_headers = {"Content-Type": "application/json"}
    if headers:
        final_headers.update(headers)

    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers=final_headers, method="POST")
    with urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
    return json.loads(body) if body else {}
