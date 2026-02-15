from __future__ import annotations

import logging

import pandas as pd

LOGGER = logging.getLogger(__name__)

SENSITIVE_FILE_HINTS = (
	"auth",
	"permission",
	"credential",
	"secret",
	"token",
	".github/workflows",
)


def run_deception_agent(pr_records: list[dict[str, object]]) -> dict[int, dict[str, object]]:
	LOGGER.info("Running deception agent on %s PRs", len(pr_records))
	output: dict[int, dict[str, object]] = {}

	for pr in pr_records:
		number = int(pr["number"])
		additions = int(pr.get("additions", 0))
		deletions = int(pr.get("deletions", 0))
		changed_files = int(pr.get("changed_files", 0))
		files = pr.get("files", [])

		risk_flags: list[str] = []
		risk_score = 0.0

		if additions + deletions > 4000:
			risk_flags.append("very_large_change")
			risk_score += 0.35

		if changed_files > 70:
			risk_flags.append("high_file_spread")
			risk_score += 0.25

		for file_item in files if isinstance(files, list) else []:
			filename = str(file_item.get("filename", "")).lower()
			if any(token in filename for token in SENSITIVE_FILE_HINTS):
				risk_flags.append("sensitive_file_touched")
				risk_score += 0.2
				break

		risk_score = min(1.0, risk_score)
		output[number] = {
			"risk_flags": sorted(set(risk_flags)),
			"risk_score": round(risk_score, 3),
		}

	LOGGER.info("Deception agent finished")
	return output


def calculate_risk(pr_df: pd.DataFrame) -> pd.DataFrame:
	"""Calculates risk/deception score (0-100) from change surface and touched files."""
	LOGGER.info("Calculating risk for %s PRs", len(pr_df))
	if pr_df.empty:
		return pd.DataFrame(columns=["pr_number", "risk_score", "risk_band"])

	rows: list[dict[str, float | int | str]] = []
	for _, pr in pr_df.iterrows():
		risk_score = 0.0
		additions = float(pr.get("additions", 0))
		deletions = float(pr.get("deletions", 0))
		changed_files = float(pr.get("changed_files", 0))
		files = pr.get("files", [])

		if additions + deletions > 4000:
			risk_score += 35
		if changed_files > 70:
			risk_score += 30
		if additions > deletions * 4 and additions > 1000:
			risk_score += 15

		if isinstance(files, list):
			for item in files:
				filename = str(item.get("filename", "")).lower()
				if any(token in filename for token in SENSITIVE_FILE_HINTS):
					risk_score += 20
					break

		risk_score = max(0.0, min(100.0, risk_score))
		band = "high" if risk_score >= 50 else "medium" if risk_score >= 20 else "low"
		rows.append(
			{
				"pr_number": int(pr["pr_number"]),
				"risk_score": round(risk_score, 2),
				"risk_band": band,
			}
		)

	risk_df = pd.DataFrame(rows)
	LOGGER.info("Risk report generated")
	return risk_df

