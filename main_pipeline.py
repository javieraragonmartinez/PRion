from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from agents.deception_agent import calculate_risk
from agents.dedupe_agent import cluster_prs
from agents.prioritization_agent import calculate_priority
from agents.trust_agent import calculate_trust
from ingestion.github_fetch import fetch_all_prs
from memory.embeddings import generate_embeddings
from outputs.github_labeler import label_prs
from outputs.webhook_delivery import deliver_webhook_payloads
from outputs.webhook_exporter import export_webhook_payloads
from prion_instructions import PRION_INSTRUCTIONS
from runtime_config import RuntimeSettings, load_settings


logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
LOGGER = logging.getLogger("prion.pipeline")


def _write_markdown_report(df: pd.DataFrame, top_prs: pd.DataFrame, output_path: Path) -> None:
	clusters = int(df["cluster"].nunique()) if "cluster" in df.columns and not df.empty else 0
	flagged_risk = int((df["risk_score"] >= 20).sum()) if "risk_score" in df.columns else 0
	flagged_attention = int((df["risk_score"] >= 30).sum()) if "risk_score" in df.columns else 0
	critical = int((df["priority_bucket"] == "critical").sum()) if "priority_bucket" in df.columns else 0

	with output_path.open("w", encoding="utf-8") as handle:
		handle.write("# PRion DAILY REPORT\n\n")
		handle.write(f"Objective: {PRION_INSTRUCTIONS['objective']}\n\n")
		handle.write(f"Total PRs: {len(df)}\n")
		handle.write(f"Clusters detected: {clusters}\n")
		handle.write(f"Critical priority PRs: {critical}\n")
		handle.write(f"Top PRs by cluster & trust: {len(top_prs)}\n")
		handle.write(f"PRs flagged as potential-risk: {flagged_risk}\n")
		handle.write(f"PRs flagged as requires-attention: {flagged_attention}\n\n")
		handle.write("CSV files available in `reports/` folder.\n")
		handle.write("Webhook payloads available for Slack/Discord/Notion in `reports/`.\n")


def _configure_logging(log_level: str) -> None:
	root = logging.getLogger()
	root.setLevel(getattr(logging, log_level.upper(), logging.INFO))


def _load_runtime() -> RuntimeSettings:
	settings = load_settings()
	_configure_logging(settings.log_level)
	return settings


def main() -> None:
	settings = _load_runtime()
	LOGGER.info("=== PRion PIPELINE START ===")
	LOGGER.info(
		"Operating mode: SHADOW_MODE=%s COMMENT_MODE=%s SHADOW_WRITES=%s",
		settings.shadow_mode,
		settings.comment_mode,
		settings.write_labels_in_shadow_mode,
	)
	LOGGER.info("Instructions loaded: %s", PRION_INSTRUCTIONS["objective"])

	try:
		LOGGER.info("1/8 Fetching all open PRs")
		pr_df = fetch_all_prs(
			settings.github_token,
			settings.repo_owner,
			settings.repo_name,
			state="open",
			max_prs=settings.max_prs,
		)

		LOGGER.info("2/8 Generating embeddings")
		embeddings_df = generate_embeddings(pr_df)

		LOGGER.info("3/8 Clustering PRs")
		cluster_report = cluster_prs(pr_df)

		LOGGER.info("4/8 Calculating trust scores")
		trust_report = calculate_trust(pr_df)

		LOGGER.info("5/8 Calculating risk/deception scores")
		risk_report = calculate_risk(pr_df)

		LOGGER.info("6/9 Merging all reports")
		df = cluster_report.merge(trust_report, on="pr_number", how="left")
		df = df.merge(risk_report, on="pr_number", how="left")
		df = df.merge(
			pr_df[["pr_number", "title", "author", "url", "comments", "review_comments", "changed_files"]],
			on="pr_number",
			how="left",
		)
		df = df.merge(embeddings_df, on="pr_number", how="left")

		LOGGER.info("7/9 Calculating composite priority")
		priority_report = calculate_priority(df)
		df = df.merge(priority_report, on="pr_number", how="left")

		LOGGER.info("8/9 Applying stealth labels")
		labeling_result = label_prs(
			df,
			github_token=settings.github_token,
			repo_owner=settings.repo_owner,
			repo_name=settings.repo_name,
			shadow_mode=settings.shadow_mode,
			allow_shadow_writes=settings.write_labels_in_shadow_mode,
		)
		LOGGER.info("Labeling summary: %s", labeling_result)

		LOGGER.info("9/9 Generating daily reports and webhook payloads")
		reports_dir = Path(settings.report_dir)
		reports_dir.mkdir(parents=True, exist_ok=True)

		daily_csv = reports_dir / "daily_report.csv"
		top_csv = reports_dir / "top_prs.csv"
		md_report = reports_dir / "daily_report.md"
		priority_csv = reports_dir / "priority_report.csv"

		df.to_csv(daily_csv, index=False)
		top_prs = df.sort_values(by=["priority_score", "risk_score"], ascending=[False, True]).head(30)
		top_prs.to_csv(top_csv, index=False)
		priority_report.to_csv(priority_csv, index=False)
		_write_markdown_report(df, top_prs, md_report)
		webhook_paths = export_webhook_payloads(df, settings.report_dir)
		webhook_delivery_status = deliver_webhook_payloads(
			webhook_paths,
			{
				"slack": settings.slack_webhook_url,
				"discord": settings.discord_webhook_url,
				"notion": settings.notion_webhook_url,
			},
			enabled=settings.enable_webhook_delivery,
			shadow_mode=settings.shadow_mode,
			allow_in_shadow_mode=settings.allow_webhook_delivery_in_shadow_mode,
		)

		LOGGER.info(
			"Reports generated: %s | %s | %s | %s | webhooks=%s | delivery=%s",
			daily_csv,
			top_csv,
			md_report,
			priority_csv,
			{provider: str(path) for provider, path in webhook_paths.items()},
			webhook_delivery_status,
		)
		LOGGER.info("=== PIPELINE COMPLETE ===")
	except Exception as exc:
		LOGGER.exception("Pipeline failed: %s", exc)
		raise


if __name__ == "__main__":
	main()