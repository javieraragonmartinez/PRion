# PRion
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Stars](https://img.shields.io/github/stars/javieraragonmartinez/PRion?style=social)](https://github.com/javieraragonmartinez/PRion/stargazers)
[![Forks](https://img.shields.io/github/forks/javieraragonmartinez/PRion?style=social)](https://github.com/javieraragonmartinez/PRion/network/members)
[![CI](https://github.com/javieraragonmartinez/PRion/actions/workflows/ci.yml/badge.svg)](https://github.com/javieraragonmartinez/PRion/actions)

PRion transforms chaotic GitHub repos into manageable workflows. It AI-clusters PRs, scores author trust, flags risks, and stealth-labels contributions helping maintainers prioritize thousands of PRs safely and efficiently from day one.

## Motivation

PRion was born as a direct response to the need expressed by the OpenClaw community in anticipation of the expected surge of pull requests following their agreement with OpenAI.

Developed in a single day with the help of Codex, this project aims to assist maintainers of repositories with high contribution volumes,
in an open and non-profit manner. It is licensed under the MIT license, allowing anyone to use or adapt it.

PRion is an AI assistant for repositories with high-volume Pull Requests.
It helps maintainers manage and prioritize contributions efficiently by:

- Clustering PRs by themes
- Evaluating trust for authors and PRs
- Detecting potential risks and malicious attempts
- Calculating advanced composite priority scores
- Applying stealth labels on GitHub
- Generating daily CSV and Markdown reports
- Exporting webhook-ready JSON payloads (Slack/Discord/Notion)

PRion is designed for repositories with very high PR volume and preserves community contributions by default.

---

## Repository Structure

```text
prion/
├── README.md
├── CHANGELOG.md
├── LICENSE
├── requirements.txt
├── config_template.py
├── runtime_config.py
├── main_pipeline.py
├── main.py
├── prion_instructions.py
├── ARCHITECTURE.md
├── VISION_GUIDELINES.md
├── CONTACT.md
├── RELEASE_V0_1_CHECKLIST.md
├── RELEASE_NOTES_v0.1.md
├── ingestion/
│   ├── __init__.py
│   └── github_fetch.py
├── memory/
│   ├── __init__.py
│   └── embeddings.py
├── agents/
│   ├── __init__.py
│   ├── dedupe_agent.py
│   ├── trust_agent.py
│   └── deception_agent.py
│   └── prioritization_agent.py
├── outputs/
│   ├── __init__.py
│   ├── github_labeler.py
│   ├── webhook_exporter.py
│   └── webhook_delivery.py
├── tests/
│   ├── conftest.py
│   ├── test_labeler.py
│   ├── test_runtime_config.py
│   ├── test_priority_and_webhooks.py
│   └── test_webhook_delivery.py
└── .github/
  └── workflows/
    └── ci.yml
└── reports/
```

---

## Installation

```bash
git clone https://github.com/yourusername/prion.git
cd prion
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Configuration

1. Copy `config_template.py` to `config.py`
2. Fill `GITHUB_TOKEN`, `REPO_OWNER`, `REPO_NAME`
3. Keep `SHADOW_MODE = True` for safe execution
4. Keep `WRITE_LABELS_IN_SHADOW_MODE = False` to run in dry-run mode (recommended)

---

## Usage

Run the full pipeline:

```bash
python main_pipeline.py
```

Reports generated:

- `reports/daily_report.csv`
- `reports/top_prs.csv`
- `reports/daily_report.md`
- `reports/priority_report.csv`
- `reports/webhook_slack.json`
- `reports/webhook_discord.json`
- `reports/webhook_notion.json`

---

## CTO Operational Contract

- No automatic PR deletion, closure, or merge
- Explainable trust/risk/cluster outputs per PR
- Full logging and auditable daily outputs
- Scalable ingestion with GitHub pagination and retry logic
- Safe-first operational mode (`SHADOW_MODE=True`)

---

## Architecture Flow

```text
GitHub PRs
  -> Data Ingestion (metadata, files, diffs, timestamps)
  -> Memory & Embeddings
  -> Agents (Dedupe, Trust, Deception/Risk)
  -> Labeling Output (dry-run or live)
  -> Daily Reports (CSV + Markdown)
  -> Founder Review / Feedback loop
```

---

## Hardening Notes

- `SHADOW_MODE=True` with `WRITE_LABELS_IN_SHADOW_MODE=False` means no GitHub write action is executed.
- `COMMENT_MODE=True` requires disabling shadow mode in runtime validation.
- `MAX_PRS` can be used to safely test on subsets before full-repo runs.
- `ENABLE_WEBHOOK_DELIVERY=False` by default keeps webhook delivery disabled.
- If webhook delivery is enabled, set at least one of: `SLACK_WEBHOOK_URL`, `DISCORD_WEBHOOK_URL`, `NOTION_WEBHOOK_URL`.
- In shadow mode, delivery is blocked unless `ALLOW_WEBHOOK_DELIVERY_IN_SHADOW_MODE=True`.

---

## Advanced Prioritization

PRion computes a composite `priority_score` (0-100) using explainable weighted signals:

- Trust score contribution
- Inverse risk contribution
- Inverse dedupe contribution
- Freshness/activity contribution

Priority buckets: `critical`, `high`, `medium`, `low`.

---

## Recommendations

- Keep `SHADOW_MODE = True` until outputs are validated
- Review reports before enabling full operational actions
- Run daily for updated clustering and prioritization

---

## Future Extensions

## Key Features

- 🔗 **Semantic clustering of PRs** by similar topics
- 👤 **Trust assessment** of authors and contributions
- ⚠️ **Risk detection** and malicious attempts
- ⭐ **Composite priority score** (0-100) for review ordering
- 🏷️ **Stealth labeling** on GitHub (shadow mode by default)
- 📊 **Daily reports** in CSV and Markdown
- 📤 **Webhooks ready** for Slack, Discord, and Notion

---

## Additional Docs

- Architecture overview: [ARCHITECTURE.md](ARCHITECTURE.md)
- Vision and review criteria: [VISION_GUIDELINES.md](VISION_GUIDELINES.md)
- Contacts: [CONTACT.md](CONTACT.md)
- Release checklist: [RELEASE_V0_1_CHECKLIST.md](RELEASE_V0_1_CHECKLIST.md)
- Release notes: [RELEASE_NOTES_v0.1.md](RELEASE_NOTES_v0.1.md)
- Changelog: [CHANGELOG.md](CHANGELOG.md)

---

## Contact

- Author email: [blkrk2025@gmail.com](mailto:blkrk2025@gmail.com)
- Author X account: @javieraragon
- PRion X account: @PRionEvo

---

## Validation Status

PRion includes unit tests and CI checks for:

- Safe shadow-mode labeling behavior
- Runtime configuration validation
- Composite priority scoring and webhook payload exports
- Optional webhook delivery guardrails and retries
