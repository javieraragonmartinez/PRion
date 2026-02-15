from __future__ import annotations

import logging

import pandas as pd

LOGGER = logging.getLogger(__name__)


def run_trust_agent(pr_records: list[dict[str, object]]) -> dict[int, dict[str, object]]:
	LOGGER.info("Running trust agent on %s PRs", len(pr_records))
	output: dict[int, dict[str, object]] = {}

	for pr in pr_records:
		number = int(pr["number"])
		score = 0.5
		reasons: list[str] = []

		draft = bool(pr.get("draft", False))
		comments = int(pr.get("comments", 0)) + int(pr.get("review_comments", 0))
		labels = [str(label).lower() for label in pr.get("labels", [])]

		if draft:
			score -= 0.1
			reasons.append("draft_pr")

		if comments >= 5:
			score += 0.1
			reasons.append("has_review_activity")

		if "hotfix" in labels:
			score -= 0.05
			reasons.append("hotfix_requires_attention")

		score = max(0.0, min(1.0, score))
		output[number] = {
			"trust_score": round(score, 3),
			"trust_reasons": reasons,
		}

	LOGGER.info("Trust agent finished")
	return output


def calculate_trust(pr_df: pd.DataFrame) -> pd.DataFrame:
	"""Calculates trust score (0-100) based on observable PR metadata."""
	LOGGER.info("Calculating trust for %s PRs", len(pr_df))
	if pr_df.empty:
		return pd.DataFrame(columns=["pr_number", "trust_score", "trust_band"])

	rows: list[dict[str, float | int | str]] = []
	for _, pr in pr_df.iterrows():
		score = 50.0
		changes = float(pr.get("additions", 0)) + float(pr.get("deletions", 0))
		engagement = float(pr.get("comments", 0)) + float(pr.get("review_comments", 0))

		if changes < 600:
			score += 12
		if changes > 3000:
			score -= 20
		if engagement >= 5:
			score += 10
		if engagement == 0:
			score -= 8

		score = max(0.0, min(100.0, score))
		band = "high" if score >= 70 else "medium" if score >= 45 else "low"
		rows.append(
			{
				"pr_number": int(pr["pr_number"]),
				"trust_score": round(score, 2),
				"trust_band": band,
			}
		)

	trust_df = pd.DataFrame(rows)
	LOGGER.info("Trust report generated")
	return trust_df

