from __future__ import annotations

import logging
from difflib import SequenceMatcher

import pandas as pd

LOGGER = logging.getLogger(__name__)


def run_dedupe_agent(pr_records: list[dict[str, object]]) -> dict[int, dict[str, object]]:
	LOGGER.info("Running dedupe agent on %s PRs", len(pr_records))
	output: dict[int, dict[str, object]] = {
		int(pr["number"]): {"potential_duplicates": [], "dedupe_score": 0.0}
		for pr in pr_records
	}

	for i, left in enumerate(pr_records):
		for right in pr_records[i + 1 :]:
			left_number = int(left["number"])
			right_number = int(right["number"])
			title_a = str(left.get("title", "")).lower()
			title_b = str(right.get("title", "")).lower()

			similarity = SequenceMatcher(a=title_a, b=title_b).ratio()
			if similarity >= 0.92:
				output[left_number]["potential_duplicates"].append(right_number)
				output[right_number]["potential_duplicates"].append(left_number)
				output[left_number]["dedupe_score"] = max(output[left_number]["dedupe_score"], similarity)
				output[right_number]["dedupe_score"] = max(output[right_number]["dedupe_score"], similarity)

	LOGGER.info("Dedupe agent finished")
	return output


def cluster_prs(pr_df: pd.DataFrame) -> pd.DataFrame:
	"""Clusters and deduplicates PRs using title similarity heuristics."""
	LOGGER.info("Clustering %s PRs", len(pr_df))
	if pr_df.empty:
		return pd.DataFrame(columns=["pr_number", "cluster", "dedupe_score", "duplicate_count"])

	titles = pr_df["title"].fillna("").astype(str).str.lower().tolist()
	clusters = list(range(len(titles)))
	dedupe_scores = [0.0 for _ in titles]
	duplicate_counts = [0 for _ in titles]

	for i, left_title in enumerate(titles):
		for j in range(i + 1, len(titles)):
			right_title = titles[j]
			similarity = SequenceMatcher(a=left_title, b=right_title).ratio()
			if similarity >= 0.92:
				clusters[j] = clusters[i]
				dedupe_scores[i] = max(dedupe_scores[i], similarity)
				dedupe_scores[j] = max(dedupe_scores[j], similarity)
				duplicate_counts[i] += 1
				duplicate_counts[j] += 1

	cluster_df = pd.DataFrame(
		{
			"pr_number": pr_df["pr_number"].astype(int).tolist(),
			"cluster": clusters,
			"dedupe_score": [round(score * 100, 2) for score in dedupe_scores],
			"duplicate_count": duplicate_counts,
		}
	)
	LOGGER.info("Cluster report generated")
	return cluster_df

