from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

LOGGER = logging.getLogger(__name__)


def _top_priority_records(df: pd.DataFrame, limit: int = 20) -> list[dict[str, Any]]:
    if df.empty:
        return []
    top = df.sort_values(by=["priority_score", "risk_score"], ascending=[False, False]).head(limit)
    return top.to_dict(orient="records")


def _base_export_payload(df: pd.DataFrame) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    high_risk = int((df.get("risk_score", pd.Series(dtype=float)) >= 50).sum()) if not df.empty else 0
    critical = int((df.get("priority_bucket", pd.Series(dtype=str)) == "critical").sum()) if not df.empty else 0
    return {
        "generated_at": now,
        "total_prs": int(len(df)),
        "critical_prs": critical,
        "high_risk_prs": high_risk,
    }


def build_slack_payload(df: pd.DataFrame) -> dict[str, Any]:
    base = _base_export_payload(df)
    top = _top_priority_records(df)
    lines = [
        f"*PRion Daily Summary*",
        f"Total PRs: {base['total_prs']}",
        f"Critical PRs: {base['critical_prs']}",
        f"High Risk PRs: {base['high_risk_prs']}",
    ]
    for item in top[:10]:
        lines.append(
            f"• #{item['pr_number']} | priority={item.get('priority_score')} | risk={item.get('risk_score')} | trust={item.get('trust_score')}"
        )
    return {
        "text": "\n".join(lines),
        "metadata": base,
        "top_prs": top,
    }


def build_discord_payload(df: pd.DataFrame) -> dict[str, Any]:
    base = _base_export_payload(df)
    top = _top_priority_records(df, limit=10)
    embed_lines = [
        {
            "name": f"PR #{item['pr_number']}",
            "value": (
                f"Priority: {item.get('priority_score')} ({item.get('priority_bucket')})\n"
                f"Risk: {item.get('risk_score')} | Trust: {item.get('trust_score')}"
            ),
            "inline": False,
        }
        for item in top
    ]
    return {
        "content": "PRion daily prioritization update",
        "embeds": [
            {
                "title": "PRion Daily Summary",
                "description": (
                    f"Total PRs: {base['total_prs']} | Critical: {base['critical_prs']} | High Risk: {base['high_risk_prs']}"
                ),
                "fields": embed_lines,
            }
        ],
        "metadata": base,
    }


def build_notion_payload(df: pd.DataFrame) -> dict[str, Any]:
    base = _base_export_payload(df)
    top = _top_priority_records(df)
    items = []
    for item in top:
        items.append(
            {
                "pr_number": item.get("pr_number"),
                "title": item.get("title"),
                "url": item.get("url"),
                "priority_score": item.get("priority_score"),
                "priority_bucket": item.get("priority_bucket"),
                "risk_score": item.get("risk_score"),
                "trust_score": item.get("trust_score"),
                "reasons": item.get("priority_reasons"),
            }
        )
    return {
        "summary": base,
        "items": items,
    }


def export_webhook_payloads(df: pd.DataFrame, reports_dir: str) -> dict[str, Path]:
    path = Path(reports_dir)
    path.mkdir(parents=True, exist_ok=True)

    payloads = {
        "slack": build_slack_payload(df),
        "discord": build_discord_payload(df),
        "notion": build_notion_payload(df),
    }

    output_paths: dict[str, Path] = {}
    for provider, payload in payloads.items():
        output = path / f"webhook_{provider}.json"
        with output.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        output_paths[provider] = output
        LOGGER.info("Webhook payload exported: %s", output)

    return output_paths
