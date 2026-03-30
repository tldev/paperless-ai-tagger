#!/bin/sh
set -e

# Provision Claude CLI credentials from environment variables.
# This lets the CLI handle its own token refresh automatically,
# instead of requiring the Python code to do manual HTTP refresh calls.

CLAUDE_DIR="$HOME/.claude"

if [ -n "$CLAUDE_OAUTH_ACCESS_TOKEN" ] && [ -n "$CLAUDE_OAUTH_REFRESH_TOKEN" ]; then
    mkdir -p "$CLAUDE_DIR"

    # Write the credentials file the CLI expects
    cat > "$CLAUDE_DIR/.credentials.json" <<CREDS
{
  "claudeAiOauth": {
    "accessToken": "$CLAUDE_OAUTH_ACCESS_TOKEN",
    "refreshToken": "$CLAUDE_OAUTH_REFRESH_TOKEN",
    "expiresAt": 0,
    "scopes": ["user:file_upload", "user:inference", "user:mcp_servers", "user:profile", "user:sessions:claude_code"],
    "subscriptionType": "max",
    "rateLimitTier": "default_claude_max_20x"
  }
}
CREDS
    chmod 600 "$CLAUDE_DIR/.credentials.json"

    # Write a minimal config file (required by CLI)
    if [ ! -f "$CLAUDE_DIR/.claude.json" ]; then
        echo '{}' > "$CLAUDE_DIR/.claude.json"
    fi

    echo "[entrypoint] Claude CLI credentials provisioned from env vars"
else
    echo "[entrypoint] No CLAUDE_OAUTH_ACCESS_TOKEN/CLAUDE_OAUTH_REFRESH_TOKEN set, skipping credential provisioning"
fi

exec "$@"
