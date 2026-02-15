from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import requests

LOGGER = logging.getLogger(__name__)


def _post_with_retry(
    session: requests.Session,
    *,
    url: str,
    payload: dict[str, Any],
    retries: int = 3,
    timeout: int = 20,
) -> None:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = session.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
            return
        except requests.RequestException as exc:
            last_error = exc
            if attempt < retries:
                sleep_seconds = 2 ** (attempt - 1)
                LOGGER.warning(
                    "Webhook delivery failed (attempt %s/%s). Retrying in %ss: %s",
                    attempt,
                    retries,
                    sleep_seconds,
                    exc,
                )
                time.sleep(sleep_seconds)
                continue
            break
    if last_error is not None:
        raise last_error


def deliver_webhook_payloads(
    payload_paths: dict[str, Path],
    webhook_urls: dict[str, str],
    *,
    enabled: bool,
    shadow_mode: bool,
    allow_in_shadow_mode: bool,
) -> dict[str, Any]:
    """Delivers webhook payload files to providers.

    Delivery is disabled by default and protected in shadow mode unless explicitly allowed.
    """
    status: dict[str, Any] = {
        "enabled": enabled,
        "shadow_mode": shadow_mode,
        "delivered": 0,
        "skipped": 0,
        "errors": 0,
        "results": {},
    }

    if not enabled:
        LOGGER.info("Webhook delivery disabled by configuration")
        return status

    if shadow_mode and not allow_in_shadow_mode:
        LOGGER.info("Webhook delivery skipped in shadow mode")
        status["skipped"] = len(payload_paths)
        for provider in payload_paths:
            status["results"][provider] = "skipped_shadow_mode"
        return status

    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})

    for provider, payload_path in payload_paths.items():
        url = webhook_urls.get(provider, "").strip()
        if not url:
            status["skipped"] += 1
            status["results"][provider] = "skipped_missing_url"
            continue

        try:
            payload = json.loads(payload_path.read_text(encoding="utf-8"))
            _post_with_retry(session, url=url, payload=payload)
            status["delivered"] += 1
            status["results"][provider] = "delivered"
            LOGGER.info("Webhook delivered to %s", provider)
        except Exception as exc:  # pragma: no cover - guarded by tests with mocks
            status["errors"] += 1
            status["results"][provider] = f"error:{exc}"
            LOGGER.error("Webhook delivery error for %s: %s", provider, exc)

    return status
