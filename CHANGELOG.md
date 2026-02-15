# Changelog

All notable changes to PRion are documented in this file.

## [0.1.0] - 2026-02-15

### Added

- High-volume GitHub PR ingestion with pagination, retries, and diff/file hydration.
- Modular agents for dedupe, trust, risk/deception, and advanced prioritization.
- Composite priority scoring with explainable reasons and rank buckets.
- Shadow-safe labeling with explicit write override.
- Daily report generation in CSV and Markdown formats.
- Webhook JSON exports for Slack, Discord, and Notion.
- Optional active webhook delivery with retry/backoff and shadow-mode guardrails.
- Runtime configuration validation and safety checks.
- Unit tests and CI workflow.
- Architecture, vision, contact, and release checklist documentation.

### Security

- Safe defaults to prevent destructive automation.
- No automatic PR close/delete/merge behavior.
- Delivery and labeling controls gated by explicit runtime settings.
