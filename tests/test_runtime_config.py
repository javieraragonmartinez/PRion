from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from runtime_config import load_settings


def test_load_settings_valid() -> None:
    fake_module = SimpleNamespace(
        GITHUB_TOKEN="abc",
        REPO_OWNER="owner",
        REPO_NAME="repo",
        SHADOW_MODE=True,
        COMMENT_MODE=False,
        MAX_PRS=100,
        REPORTS_DIR="reports",
        LOG_LEVEL="DEBUG",
        WRITE_LABELS_IN_SHADOW_MODE=False,
        ENABLE_WEBHOOK_DELIVERY=False,
        ALLOW_WEBHOOK_DELIVERY_IN_SHADOW_MODE=False,
        SLACK_WEBHOOK_URL="",
        DISCORD_WEBHOOK_URL="",
        NOTION_WEBHOOK_URL="",
    )
    with patch("runtime_config._read_config_module", return_value=fake_module):
        settings = load_settings()

    assert settings.repo_owner == "owner"
    assert settings.max_prs == 100


def test_load_settings_invalid_modes() -> None:
    fake_module = SimpleNamespace(
        GITHUB_TOKEN="abc",
        REPO_OWNER="owner",
        REPO_NAME="repo",
        SHADOW_MODE=True,
        COMMENT_MODE=True,
    )
    with patch("runtime_config._read_config_module", return_value=fake_module):
        with pytest.raises(ValueError):
            load_settings()


def test_load_settings_missing_credentials() -> None:
    fake_module = SimpleNamespace(GITHUB_TOKEN="", REPO_OWNER="", REPO_NAME="")
    with patch("runtime_config._read_config_module", return_value=fake_module):
        with pytest.raises(ValueError):
            load_settings()


def test_load_settings_webhook_enabled_requires_url() -> None:
    fake_module = SimpleNamespace(
        GITHUB_TOKEN="abc",
        REPO_OWNER="owner",
        REPO_NAME="repo",
        SHADOW_MODE=True,
        COMMENT_MODE=False,
        ENABLE_WEBHOOK_DELIVERY=True,
        SLACK_WEBHOOK_URL="",
        DISCORD_WEBHOOK_URL="",
        NOTION_WEBHOOK_URL="",
    )
    with patch("runtime_config._read_config_module", return_value=fake_module):
        with pytest.raises(ValueError):
            load_settings()