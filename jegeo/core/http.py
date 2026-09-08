"""Thin HTTP helper shared by every module that reaches out to a public API.

Centralizing this means every online lookup gets the same timeout, the same
identifying User-Agent (so we're not silently spoofing a browser), and the
same error surface — callers just catch ``Exception`` and show it in the
console rather than each module reinventing retry/timeout policy.
"""
from __future__ import annotations

import requests

DEFAULT_TIMEOUT = 12
USER_AGENT = "JegeoPayload/1.0 (+https://github.com/; personal OSINT toolkit)"


def _headers(extra: dict | None) -> dict:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json, text/plain, */*"}
    if extra:
        headers.update(extra)
    return headers


def get_json(url: str, params: dict | None = None, headers: dict | None = None,
             timeout: float = DEFAULT_TIMEOUT):
    resp = requests.get(url, params=params, headers=_headers(headers), timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def get_text(url: str, params: dict | None = None, headers: dict | None = None,
              timeout: float = DEFAULT_TIMEOUT) -> str:
    resp = requests.get(url, params=params, headers=_headers(headers), timeout=timeout)
    resp.raise_for_status()
    return resp.text


def probe(url: str, timeout: float = 6.0) -> tuple[int | None, str]:
    """GET a URL and return (status_code, body_text) without raising on a
    non-2xx response — for callers like Username Recon where a 404 is a
    normal, expected outcome rather than an error. Returns (None, "") on
    any connection-level failure (timeout, DNS, refused, etc.)."""
    try:
        resp = requests.get(url, headers=_headers(None), timeout=timeout, allow_redirects=True)
        return resp.status_code, resp.text
    except requests.RequestException:
        return None, ""
