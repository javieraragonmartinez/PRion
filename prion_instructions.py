from __future__ import annotations

from typing import Any


"""
PRion — AI Instructions / CTO Guidelines

This module contains the full operational instructions for the PRion code AI,
including objectives, pipeline behavior, modules, scoring, labeling, and future roadmap.
"""


PRION_INSTRUCTIONS: dict[str, Any] = {
    "objective": (
        "Manage high-volume GitHub repositories (>3000 PRs). "
        "Cluster, prioritize, and assess PRs efficiently. "
        "Maintain community trust: PRs are never deleted blindly, only flagged or labeled."
    ),
    "pipeline": {
        "data_ingestion": (
            "Fetch all open PRs from GitHub, including author, title, description, files, diffs, and timestamps. "
            "Store for clustering and scoring. Support future scalability (>10k PRs)."
        ),
        "memory_embeddings": (
            "Generate embeddings based on PR text (title/description) and code diffs and labels. "
            "Use embeddings for clustering and similarity detection."
        ),
    },
    "agents": {
        "dedupe_agent": (
            "Detect duplicate or highly similar PRs. "
            "Cluster them and suggest merging or flagging while keeping authorship visible."
        ),
        "trust_agent": (
            "Score authors based on historical reliability and PR quality. "
            "Score PRs based on size, complexity, and author trust."
        ),
        "deception_agent": (
            "Detect potentially malicious PRs: backdoors, unsafe dependencies, phishing, injection patterns. "
            "Assign a risk score to each PR."
        ),
        "labeling_agent": (
            "Apply stealth labels for cluster, risk, and trust. "
            "Optionally suggest comments for founder review. "
            "Do not close or delete PRs automatically."
        ),
    },
    "reporting": (
        "Generate daily reports (CSV and Markdown) including: "
        "total PRs, clusters detected, top PRs by cluster/trust, PRs flagged for potential risk or attention. "
        "Reports must be human-readable, auditable, and compatible with Slack/email notifications."
    ),
    "modes": {
        "shadow_mode": "True = dry-run by default, no visible GitHub write actions.",
        "comment_mode": "True = visible comments and labels. Activate only after validation.",
        "daily_execution": "Run the pipeline daily to maintain up-to-date clustering and scoring.",
    },
    "security": (
        "Safe execution: no automatic PR merging or closure initially. "
        "Log all PR actions for auditing. "
        "Scalable to tens of thousands of PRs."
    ),
    "future_extensions": {
        "deep_semantic_review": (
            "Use embeddings + LLM to understand code intent and detect PRs that stray from project vision."
        ),
        "prioritization": (
            "Highlight PRs for early merge or critical review based on trust and risk scores."
        ),
        "dashboard": (
            "Interactive UI to explore clusters, trust, risk, and top PRs. "
            "Filterable by author, cluster, or score."
        ),
        "communication_integration": (
            "Send daily alerts via Slack, Discord, or email for critical or suspicious PRs."
        ),
        "continuous_learning": (
            "Founder feedback loop: mark PRs as approved or rejected. "
            "Adjust trust and risk scoring automatically over time."
        ),
    },
    "ai_guidelines": (
        "Always preserve community contributions. "
        "Prioritize transparency: every label or risk flag must be explainable. "
        "Focus on trust and risk first, then suggest actions. "
        "Avoid aggressive automation until validated. "
        "Ensure efficient scaling and handle sudden PR volume spikes."
    ),
    "flow_ascii": (
        "GitHub PRs -> Data Ingestion -> Memory & Embeddings -> "
        "Agents(Dedupe/Trust/Deception/Labeling) -> Reporting -> Founder Review -> Learning Loop"
    ),
}
