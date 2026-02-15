# PRion configuration template for the founder

GITHUB_TOKEN = ""          # GitHub token with PR permissions
REPO_OWNER = ""            # Repository owner
REPO_NAME = ""             # Repository name

# Modes
SHADOW_MODE = True         # True = stealth labeling, no comments or closure
COMMENT_MODE = False       # True = visible comments and labels

# Runtime controls
MAX_PRS = None             # Optional int limit, e.g. 500 for dry runs
REPORTS_DIR = "reports"
LOG_LEVEL = "INFO"

# Safety controls
# In SHADOW_MODE this should remain False to avoid visible writes to GitHub.
WRITE_LABELS_IN_SHADOW_MODE = False

# Webhook delivery controls (optional, default-safe)
ENABLE_WEBHOOK_DELIVERY = False
ALLOW_WEBHOOK_DELIVERY_IN_SHADOW_MODE = False
SLACK_WEBHOOK_URL = ""
DISCORD_WEBHOOK_URL = ""
NOTION_WEBHOOK_URL = ""