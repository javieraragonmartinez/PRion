from __future__ import annotations

import logging
from dataclasses import dataclass

import pandas as pd

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class PriorityWeights:
    trust_weight: float = 0.45
    risk_weight: float = 0.35
    dedupe_weight: float = 0.10
    freshness_weight: float = 0.10


def _clamp(value: float, lower: float = 0.0, upper: float = 100.0) -> float:
    return max(lower, min(upper, value))


def _priority_bucket(score: float) -> str:
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def _freshness_signal(row: pd.Series) -> float:
    comments = float(row.get("comments", 0)) + float(row.get("review_comments", 0))
    changed_files = float(row.get("changed_files", 0))
    recency_bonus = 20.0 if comments >= 4 else 10.0 if comments >= 1 else 0.0
    complexity_penalty = 15.0 if changed_files > 70 else 0.0
    return _clamp(50.0 + recency_bonus - complexity_penalty)


def calculate_priority(
    df: pd.DataFrame,
    *,
    weights: PriorityWeights | None = None,
) -> pd.DataFrame:
    """Calculates explainable composite priority score for each PR.

    Higher scores mean higher review priority.
    """
    LOGGER.info("Calculating advanced priority for %s PRs", len(df))
    if df.empty:
        return pd.DataFrame(
            columns=[
                "pr_number",
                "priority_score",
                "priority_bucket",
                "priority_rank",
                "priority_reasons",
            ]
        )

    selected_weights = weights or PriorityWeights()
    rows: list[dict[str, object]] = []

    for _, row in df.iterrows():
        pr_number = int(row["pr_number"])
        trust_score = _clamp(float(row.get("trust_score", 50.0)))
        risk_score = _clamp(float(row.get("risk_score", 0.0)))
        dedupe_score = _clamp(float(row.get("dedupe_score", 0.0)))
        freshness_score = _freshness_signal(row)

        trust_component = selected_weights.trust_weight * trust_score
        risk_component = selected_weights.risk_weight * (100.0 - risk_score)
        dedupe_component = selected_weights.dedupe_weight * (100.0 - dedupe_score)
        freshness_component = selected_weights.freshness_weight * freshness_score

        composite = _clamp(
            trust_component + risk_component + dedupe_component + freshness_component
        )

        reasons: list[str] = []
        if trust_score >= 70:
            reasons.append("high_trust")
        if risk_score >= 50:
            reasons.append("high_risk")
        if dedupe_score >= 60:
            reasons.append("possible_duplicate")
        if freshness_score >= 60:
            reasons.append("active_discussion")
        if not reasons:
            reasons.append("balanced_profile")

        rows.append(
            {
                "pr_number": pr_number,
                "priority_score": round(composite, 2),
                "priority_bucket": _priority_bucket(composite),
                "priority_reasons": ",".join(reasons),
            }
        )

    priority_df = pd.DataFrame(rows).sort_values(
        by=["priority_score", "pr_number"], ascending=[False, True]
    )
    priority_df["priority_rank"] = range(1, len(priority_df) + 1)
    priority_df = priority_df[
        [
            "pr_number",
            "priority_score",
            "priority_bucket",
            "priority_rank",
            "priority_reasons",
        ]
    ]
    LOGGER.info("Priority report generated")
    return priority_df
