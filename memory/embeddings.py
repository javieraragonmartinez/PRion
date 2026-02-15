from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class EmbeddingDocument:
	doc_id: str
	text: str
	metadata: dict[str, object]
	vector: list[float]


def _deterministic_vector(text: str, dimensions: int = 32) -> list[float]:
	digest = hashlib.sha256(text.encode("utf-8")).digest()
	vector: list[float] = []
	while len(vector) < dimensions:
		for byte in digest:
			vector.append((byte / 255.0) * 2 - 1)
			if len(vector) >= dimensions:
				break
	return vector


def build_embedding_documents(pr_storage_records: list[dict[str, object]]) -> list[EmbeddingDocument]:
	LOGGER.info("Building embedding documents for %s pull requests", len(pr_storage_records))
	documents: list[EmbeddingDocument] = []

	for pr in pr_storage_records:
		metadata = dict(pr.get("metadata", {}))
		content = pr.get("content", {})
		body = content.get("body", "") if isinstance(content, dict) else ""
		diff = content.get("diff", "") if isinstance(content, dict) else ""
		text = f"{metadata.get('title', '')}\n\n{body}\n\n{diff}".strip()

		doc = EmbeddingDocument(
			doc_id=str(pr.get("id", "")),
			text=text,
			metadata=metadata,
			vector=_deterministic_vector(text),
		)
		documents.append(doc)

	LOGGER.info("Embedding document generation complete: %s docs", len(documents))
	return documents


def generate_embeddings(pr_df: pd.DataFrame) -> pd.DataFrame:
	"""Builds deterministic embedding features for each PR row."""
	LOGGER.info("Generating embeddings for %s PR rows", len(pr_df))
	if pr_df.empty:
		return pd.DataFrame(columns=["pr_number", "embedding_norm", "embedding_dim"])

	rows: list[dict[str, float | int]] = []
	for _, row in pr_df.iterrows():
		text = f"{row.get('title', '')}\n{row.get('body', '')}\n{row.get('combined_diff', '')}"
		vector = np.array(_deterministic_vector(str(text), dimensions=64), dtype=float)
		norm = float(np.linalg.norm(vector))
		rows.append(
			{
				"pr_number": int(row["pr_number"]),
				"embedding_norm": round(norm, 6),
				"embedding_dim": int(vector.size),
			}
		)

	embeddings_df = pd.DataFrame(rows)
	LOGGER.info("Embeddings ready: %s rows", len(embeddings_df))
	return embeddings_df

