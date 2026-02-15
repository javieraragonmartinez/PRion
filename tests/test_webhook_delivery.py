from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from outputs.webhook_delivery import deliver_webhook_payloads


def _write_payload(path: Path, name: str) -> Path:
    target = path / f"webhook_{name}.json"
    target.write_text(json.dumps({"ok": True}), encoding="utf-8")
    return target


def test_delivery_disabled(tmp_path) -> None:
    payloads = {"slack": _write_payload(tmp_path, "slack")}
    result = deliver_webhook_payloads(
        payloads,
        {"slack": "https://example.com"},
        enabled=False,
        shadow_mode=True,
        allow_in_shadow_mode=False,
    )
    assert result["enabled"] is False
    assert result["delivered"] == 0


def test_delivery_shadow_skipped(tmp_path) -> None:
    payloads = {"slack": _write_payload(tmp_path, "slack")}
    result = deliver_webhook_payloads(
        payloads,
        {"slack": "https://example.com"},
        enabled=True,
        shadow_mode=True,
        allow_in_shadow_mode=False,
    )
    assert result["skipped"] == 1
    assert result["results"]["slack"] == "skipped_shadow_mode"


def test_delivery_live_success(tmp_path) -> None:
    payloads = {"slack": _write_payload(tmp_path, "slack")}
    with patch("outputs.webhook_delivery.requests.Session.post") as mocked_post:
        mocked_post.return_value.raise_for_status.return_value = None
        result = deliver_webhook_payloads(
            payloads,
            {"slack": "https://example.com"},
            enabled=True,
            shadow_mode=False,
            allow_in_shadow_mode=False,
        )

    assert mocked_post.call_count == 1
    assert result["delivered"] == 1
    assert result["errors"] == 0