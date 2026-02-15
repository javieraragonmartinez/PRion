from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module


@dataclass(slots=True)
class RuntimeSettings:
    github_token: str
    repo_owner: str
    repo_name: str
    shadow_mode: bool
    comment_mode: bool
    max_prs: int | None
    report_dir: str
    log_level: str
    write_labels_in_shadow_mode: bool
    enable_webhook_delivery: bool
    allow_webhook_delivery_in_shadow_mode: bool
    slack_webhook_url: str
    discord_webhook_url: str
    notion_webhook_url: str


def _read_config_module() -> object:
    try:
        return import_module("config")
    except ImportError:
        return import_module("config_template")


def load_settings() -> RuntimeSettings:
    config = _read_config_module()

    token = str(getattr(config, "GITHUB_TOKEN", ""))
    owner = str(getattr(config, "REPO_OWNER", ""))
    repo = str(getattr(config, "REPO_NAME", ""))

    shadow_mode = bool(getattr(config, "SHADOW_MODE", True))
    comment_mode = bool(getattr(config, "COMMENT_MODE", False))
    max_prs = getattr(config, "MAX_PRS", None)
    report_dir = str(getattr(config, "REPORTS_DIR", "reports"))
    log_level = str(getattr(config, "LOG_LEVEL", "INFO"))
    write_labels_in_shadow = bool(getattr(config, "WRITE_LABELS_IN_SHADOW_MODE", False))
    enable_webhook_delivery = bool(getattr(config, "ENABLE_WEBHOOK_DELIVERY", False))
    allow_webhook_delivery_in_shadow_mode = bool(
        getattr(config, "ALLOW_WEBHOOK_DELIVERY_IN_SHADOW_MODE", False)
    )
    slack_webhook_url = str(getattr(config, "SLACK_WEBHOOK_URL", ""))
    discord_webhook_url = str(getattr(config, "DISCORD_WEBHOOK_URL", ""))
    notion_webhook_url = str(getattr(config, "NOTION_WEBHOOK_URL", ""))

    if max_prs is not None:
        max_prs = int(max_prs)
        if max_prs <= 0:
            raise ValueError("MAX_PRS must be positive if provided")

    if not token or not owner or not repo:
        raise ValueError(
            "Missing GitHub credentials. Set GITHUB_TOKEN, REPO_OWNER and REPO_NAME in config.py/config_template.py"
        )

    if comment_mode and shadow_mode:
        raise ValueError("COMMENT_MODE=True requires SHADOW_MODE=False for safety")

    if enable_webhook_delivery:
        if not any([slack_webhook_url, discord_webhook_url, notion_webhook_url]):
            raise ValueError(
                "ENABLE_WEBHOOK_DELIVERY=True requires at least one provider webhook URL"
            )

    return RuntimeSettings(
        github_token=token,
        repo_owner=owner,
        repo_name=repo,
        shadow_mode=shadow_mode,
        comment_mode=comment_mode,
        max_prs=max_prs,
        report_dir=report_dir,
        log_level=log_level,
        write_labels_in_shadow_mode=write_labels_in_shadow,
        enable_webhook_delivery=enable_webhook_delivery,
        allow_webhook_delivery_in_shadow_mode=allow_webhook_delivery_in_shadow_mode,
        slack_webhook_url=slack_webhook_url,
        discord_webhook_url=discord_webhook_url,
        notion_webhook_url=notion_webhook_url,
    )
