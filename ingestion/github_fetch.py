from __future__ import annotations

import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import requests

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class GitHubRepoConfig:
	token: str
	owner: str
	repo: str
	api_base_url: str = "https://api.github.com"
	timeout_seconds: int = 30
	max_retries: int = 4


@dataclass(slots=True)
class PullRequestFile:
	filename: str
	status: str
	additions: int
	deletions: int
	changes: int
	patch: str
	blob_url: str
	raw_url: str


@dataclass(slots=True)
class PullRequestRecord:
	number: int
	title: str
	state: str
	draft: bool
	user_login: str
	created_at: str
	updated_at: str
	merged_at: str | None
	html_url: str
	body: str
	labels: list[str]
	additions: int
	deletions: int
	changed_files: int
	commits: int
	comments: int
	review_comments: int
	files: list[PullRequestFile]
	combined_diff: str


class GitHubPullRequestIngestor:
	def __init__(self, config: GitHubRepoConfig) -> None:
		self.config = config
		self.session = requests.Session()
		self.session.headers.update(
			{
				"Accept": "application/vnd.github+json",
				"Authorization": f"Bearer {config.token}",
				"X-GitHub-Api-Version": "2022-11-28",
			}
		)

	def _request(
		self,
		method: str,
		url: str,
		params: dict[str, Any] | None = None,
	) -> requests.Response:
		attempt = 0
		while True:
			attempt += 1
			response = self.session.request(
				method=method,
				url=url,
				params=params,
				timeout=self.config.timeout_seconds,
			)

			if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
				reset_at = int(response.headers.get("X-RateLimit-Reset", "0"))
				now = int(time.time())
				sleep_seconds = max(1, reset_at - now + 1)
				LOGGER.warning(
					"GitHub rate limit reached. Sleeping %s seconds before retry.",
					sleep_seconds,
				)
				time.sleep(sleep_seconds)
				continue

			if response.status_code >= 500 and attempt < self.config.max_retries:
				backoff = 2**attempt
				LOGGER.warning(
					"GitHub server error (%s). Retry %s/%s in %ss.",
					response.status_code,
					attempt,
					self.config.max_retries,
					backoff,
				)
				time.sleep(backoff)
				continue

			response.raise_for_status()
			return response

	def _paginate(
		self,
		url: str,
		params: dict[str, Any] | None = None,
	) -> list[dict[str, Any]]:
		items: list[dict[str, Any]] = []
		current_url = url
		current_params = params

		while current_url:
			response = self._request("GET", current_url, current_params)
			page_payload = response.json()
			if not isinstance(page_payload, list):
				raise ValueError("GitHub pagination expected list payload")

			items.extend(page_payload)
			links = response.links
			next_link = links.get("next", {}).get("url")
			current_url = next_link
			current_params = None

			LOGGER.debug("Fetched page with %s records from %s", len(page_payload), url)

		return items

	def _fetch_pr_files(self, pr_number: int) -> list[PullRequestFile]:
		files_url = (
			f"{self.config.api_base_url}/repos/{self.config.owner}/{self.config.repo}/pulls/{pr_number}/files"
		)
		raw_files = self._paginate(files_url, params={"per_page": 100})

		files: list[PullRequestFile] = []
		for file_data in raw_files:
			files.append(
				PullRequestFile(
					filename=file_data.get("filename", ""),
					status=file_data.get("status", ""),
					additions=int(file_data.get("additions", 0)),
					deletions=int(file_data.get("deletions", 0)),
					changes=int(file_data.get("changes", 0)),
					patch=file_data.get("patch") or "",
					blob_url=file_data.get("blob_url") or "",
					raw_url=file_data.get("raw_url") or "",
				)
			)
		return files

	def fetch_pull_requests(
		self,
		*,
		state: str = "all",
		sort: str = "updated",
		direction: str = "desc",
		since: datetime | None = None,
		max_prs: int | None = None,
		include_files: bool = True,
	) -> list[dict[str, Any]]:
		pulls_url = f"{self.config.api_base_url}/repos/{self.config.owner}/{self.config.repo}/pulls"
		params: dict[str, Any] = {
			"state": state,
			"sort": sort,
			"direction": direction,
			"per_page": 100,
		}
		if since is not None:
			params["since"] = since.astimezone(timezone.utc).isoformat()

		LOGGER.info(
			"Starting PR ingestion for %s/%s (state=%s, max_prs=%s)",
			self.config.owner,
			self.config.repo,
			state,
			max_prs,
		)

		pull_summaries = self._paginate(pulls_url, params=params)
		LOGGER.info("Fetched %s PR summaries from GitHub", len(pull_summaries))

		results: list[dict[str, Any]] = []
		for idx, pr in enumerate(pull_summaries, start=1):
			pr_number = int(pr["number"])
			if max_prs is not None and len(results) >= max_prs:
				break

			LOGGER.info("Hydrating PR #%s (%s/%s)", pr_number, idx, len(pull_summaries))
			detail_url = f"{self.config.api_base_url}/repos/{self.config.owner}/{self.config.repo}/pulls/{pr_number}"
			detail = self._request("GET", detail_url).json()

			files = self._fetch_pr_files(pr_number) if include_files else []
			combined_diff = "\n\n".join(file.patch for file in files if file.patch)

			record = PullRequestRecord(
				number=pr_number,
				title=detail.get("title") or "",
				state=detail.get("state") or "",
				draft=bool(detail.get("draft", False)),
				user_login=(detail.get("user") or {}).get("login") or "",
				created_at=detail.get("created_at") or "",
				updated_at=detail.get("updated_at") or "",
				merged_at=detail.get("merged_at"),
				html_url=detail.get("html_url") or "",
				body=detail.get("body") or "",
				labels=[label.get("name", "") for label in detail.get("labels", [])],
				additions=int(detail.get("additions", 0)),
				deletions=int(detail.get("deletions", 0)),
				changed_files=int(detail.get("changed_files", 0)),
				commits=int(detail.get("commits", 0)),
				comments=int(detail.get("comments", 0)),
				review_comments=int(detail.get("review_comments", 0)),
				files=files,
				combined_diff=combined_diff,
			)
			results.append(asdict(record))

		LOGGER.info("Completed PR ingestion. Total hydrated PRs: %s", len(results))
		return results


def transform_for_storage(pr_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
	transformed: list[dict[str, Any]] = []
	for pr in pr_records:
		transformed.append(
			{
				"id": f"pr_{pr['number']}",
				"metadata": {
					"number": pr["number"],
					"title": pr["title"],
					"state": pr["state"],
					"author": pr["user_login"],
					"updated_at": pr["updated_at"],
					"labels": pr["labels"],
					"changed_files": pr["changed_files"],
					"additions": pr["additions"],
					"deletions": pr["deletions"],
				},
				"content": {
					"body": pr["body"],
					"diff": pr["combined_diff"],
					"files": pr["files"],
				},
			}
		)
	return transformed


def fetch_all_prs(
	token: str,
	owner: str,
	repo: str,
	*,
	state: str = "open",
	max_prs: int | None = None,
) -> pd.DataFrame:
	"""Fetches pull requests from GitHub and returns a normalized DataFrame."""
	if not token or not owner or not repo:
		raise ValueError("token, owner and repo are required")

	config = GitHubRepoConfig(token=token, owner=owner, repo=repo)
	ingestor = GitHubPullRequestIngestor(config)
	pr_records = ingestor.fetch_pull_requests(
		state=state,
		max_prs=max_prs,
		include_files=True,
	)

	if not pr_records:
		return pd.DataFrame(
			columns=[
				"pr_number",
				"title",
				"state",
				"author",
				"created_at",
				"updated_at",
				"url",
				"labels",
				"additions",
				"deletions",
				"changed_files",
				"comments",
				"review_comments",
				"body",
				"combined_diff",
				"files",
			]
		)

	rows: list[dict[str, Any]] = []
	for item in pr_records:
		rows.append(
			{
				"pr_number": item["number"],
				"title": item["title"],
				"state": item["state"],
				"author": item["user_login"],
				"created_at": item["created_at"],
				"updated_at": item["updated_at"],
				"url": item["html_url"],
				"labels": item.get("labels", []),
				"additions": item["additions"],
				"deletions": item["deletions"],
				"changed_files": item["changed_files"],
				"comments": item["comments"],
				"review_comments": item["review_comments"],
				"body": item["body"],
				"combined_diff": item["combined_diff"],
				"files": item["files"],
			}
		)

	df = pd.DataFrame(rows)
	LOGGER.info("fetch_all_prs generated dataframe with %s rows", len(df))
	return df

