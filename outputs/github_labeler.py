from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import requests

LOGGER = logging.getLogger(__name__)


def _labels_for_row(row: pd.Series) -> list[str]:
	labels: list[str] = []
	risk_score = float(row.get("risk_score", 0))
	trust_score = float(row.get("trust_score", 50))
	duplicate_count = int(row.get("duplicate_count", 0))

	if risk_score >= 30:
		labels.append("requires-attention")
	if risk_score >= 20:
		labels.append("potential-risk")
	if trust_score < 45:
		labels.append("low-trust")
	if duplicate_count > 0:
		labels.append("possible-duplicate")

	cluster = row.get("cluster")
	if cluster is not None:
		labels.append(f"cluster:{cluster}")

	return sorted(set(labels))


def label_prs(
	df: pd.DataFrame,
	*,
	github_token: str,
	repo_owner: str,
	repo_name: str,
	shadow_mode: bool = True,
	allow_shadow_writes: bool = False,
) -> dict[str, Any]:
	"""Applies labels to GitHub PRs (issues endpoint) with safe shadow-mode behavior."""
	if df.empty:
		LOGGER.info("No PRs available for labeling")
		return {"processed": 0, "labeled": 0, "errors": 0, "dry_run": shadow_mode}

	if not github_token or not repo_owner or not repo_name:
		raise ValueError("GitHub token and repository coordinates are required for labeling")

	session = requests.Session()
	session.headers.update(
		{
			"Accept": "application/vnd.github+json",
			"Authorization": f"Bearer {github_token}",
			"X-GitHub-Api-Version": "2022-11-28",
		}
	)

	processed = 0
	labeled = 0
	dry_run_actions = 0
	errors = 0

	for _, row in df.iterrows():
		processed += 1
		pr_number = int(row["pr_number"])
		labels = _labels_for_row(row)
		if not labels:
			continue

		endpoint = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{pr_number}/labels"
		payload = {"labels": labels}

		if shadow_mode and not allow_shadow_writes:
			dry_run_actions += 1
			LOGGER.info("[SHADOW-DRYRUN] PR #%s would be labeled with %s", pr_number, labels)
			continue

		try:
			response = session.post(endpoint, json=payload, timeout=30)
			response.raise_for_status()
			labeled += 1
			mode = "SHADOW-WRITE" if shadow_mode else "LIVE"
			LOGGER.info("[%s] Labeled PR #%s with %s", mode, pr_number, labels)
		except requests.RequestException as exc:
			errors += 1
			LOGGER.error("Failed labeling PR #%s: %s", pr_number, exc)

	return {
		"processed": processed,
		"labeled": labeled,
		"dry_run_actions": dry_run_actions,
		"errors": errors,
		"dry_run": shadow_mode and not allow_shadow_writes,
	}

