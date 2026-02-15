from __future__ import annotations

from unittest.mock import patch

import pandas as pd

from outputs.github_labeler import label_prs


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "pr_number": 101,
                "risk_score": 35,
                "trust_score": 40,
                "duplicate_count": 1,
                "cluster": 2,
            }
        ]
    )


def test_label_prs_shadow_mode_does_not_write() -> None:
    df = _sample_df()

    with patch("outputs.github_labeler.requests.Session.post") as mocked_post:
        result = label_prs(
            df,
            github_token="token",
            repo_owner="owner",
            repo_name="repo",
            shadow_mode=True,
            allow_shadow_writes=False,
        )

    assert mocked_post.call_count == 0
    assert result["dry_run"] is True
    assert result["dry_run_actions"] == 1
    assert result["labeled"] == 0


def test_label_prs_live_mode_writes() -> None:
    df = _sample_df()

    with patch("outputs.github_labeler.requests.Session.post") as mocked_post:
        mocked_post.return_value.raise_for_status.return_value = None
        result = label_prs(
            df,
            github_token="token",
            repo_owner="owner",
            repo_name="repo",
            shadow_mode=False,
            allow_shadow_writes=True,
        )

    assert mocked_post.call_count == 1
    assert result["dry_run"] is False
    assert result["labeled"] == 1