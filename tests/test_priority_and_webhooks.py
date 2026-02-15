from __future__ import annotations

import json

import pandas as pd

from agents.prioritization_agent import calculate_priority
from outputs.webhook_exporter import (
    build_discord_payload,
    build_notion_payload,
    build_slack_payload,
    export_webhook_payloads,
)


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "pr_number": 1,
                "title": "fix auth",
                "url": "https://example/pr/1",
                "trust_score": 85,
                "risk_score": 10,
                "dedupe_score": 0,
                "comments": 5,
                "review_comments": 2,
                "changed_files": 8,
            },
            {
                "pr_number": 2,
                "title": "mass refactor",
                "url": "https://example/pr/2",
                "trust_score": 40,
                "risk_score": 70,
                "dedupe_score": 20,
                "comments": 0,
                "review_comments": 0,
                "changed_files": 100,
            },
        ]
    )


def test_calculate_priority_ranks_expected_order() -> None:
    df = _sample_df()
    priority_df = calculate_priority(df)

    assert list(priority_df.columns) == [
        "pr_number",
        "priority_score",
        "priority_bucket",
        "priority_rank",
        "priority_reasons",
    ]
    assert int(priority_df.iloc[0]["pr_number"]) == 1
    assert int(priority_df.iloc[0]["priority_rank"]) == 1


def test_webhook_payload_builders() -> None:
    df = _sample_df()
    priority_df = calculate_priority(df)
    enriched = df.merge(priority_df, on="pr_number", how="left")

    slack_payload = build_slack_payload(enriched)
    discord_payload = build_discord_payload(enriched)
    notion_payload = build_notion_payload(enriched)

    assert "text" in slack_payload
    assert "embeds" in discord_payload
    assert "items" in notion_payload


def test_export_webhook_payloads(tmp_path) -> None:
    df = _sample_df()
    priority_df = calculate_priority(df)
    enriched = df.merge(priority_df, on="pr_number", how="left")

    paths = export_webhook_payloads(enriched, str(tmp_path))
    assert {"slack", "discord", "notion"}.issubset(paths.keys())

    for target in paths.values():
        assert target.exists()
        content = json.loads(target.read_text(encoding="utf-8"))
        assert isinstance(content, dict)