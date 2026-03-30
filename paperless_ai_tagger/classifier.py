import json
import logging
import os
import re
import shutil
import subprocess

from paperless_ai_tagger.models import Classification
from paperless_ai_tagger.oauth import ensure_fresh_token
from paperless_ai_tagger.prompt import CLASSIFICATION_SCHEMA, build_prompt

logger = logging.getLogger(__name__)


class ClassificationError(Exception):
    pass


class Classifier:
    def __init__(
        self,
        model: str = "sonnet",
        oauth_access_token: str | None = None,
        oauth_refresh_token: str | None = None,
    ):
        self.model = model
        self.oauth_access_token = oauth_access_token
        self.oauth_refresh_token = oauth_refresh_token
        self._verify_claude_cli()

    def _verify_claude_cli(self):
        if not shutil.which("claude"):
            raise ClassificationError(
                "claude CLI not found in PATH. "
                "Install it with: npm install -g @anthropic-ai/claude-code"
            )

    def classify(
        self,
        content: str,
        tags: list[str],
        correspondents: list[str],
        document_types: list[str],
        custom_prompt: str = "",
        max_content_length: int = 50000,
    ) -> Classification:
        prompt = build_prompt(
            content=content,
            tags=tags,
            correspondents=correspondents,
            document_types=document_types,
            custom_prompt=custom_prompt,
            max_content_length=max_content_length,
        )

        schema_json = json.dumps(CLASSIFICATION_SCHEMA)

        cmd = [
            "claude",
            "-p",
            "--output-format",
            "json",
            "--json-schema",
            schema_json,
            "--model",
            self.model,
            "--max-turns",
            "3",
            "--no-session-persistence",
        ]

        logger.debug("Running claude CLI with model=%s", self.model)

        # Build subprocess environment with fresh OAuth token if configured
        env = None
        if self.oauth_refresh_token:
            access_token = self.oauth_access_token or os.environ.get(
                "CLAUDE_CODE_OAUTH_TOKEN", ""
            )
            fresh_token = ensure_fresh_token(access_token, self.oauth_refresh_token)
            env = {**os.environ, "CLAUDE_CODE_OAUTH_TOKEN": fresh_token}

        try:
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=120,
                env=env,
            )
        except subprocess.TimeoutExpired:
            raise ClassificationError("claude CLI timed out after 120 seconds")

        logger.debug("Claude CLI stdout: %s", result.stdout[:2000])
        if result.stderr:
            logger.debug("Claude CLI stderr: %s", result.stderr[:1000])

        if result.returncode != 0:
            raise ClassificationError(
                f"claude CLI exited with code {result.returncode}: {result.stderr.strip()}"
            )

        try:
            envelope = json.loads(result.stdout)
        except json.JSONDecodeError:
            raise ClassificationError(
                f"Failed to parse claude CLI output as JSON: {result.stdout[:500]}"
            )

        # Check for max turns error
        if envelope.get("subtype") == "error_max_turns":
            raise ClassificationError(
                "Claude CLI hit max turns limit before producing output. "
                f"Cost: ${envelope.get('total_cost_usd', 0):.4f}"
            )

        # The --output-format json wraps the result in an envelope.
        # With --json-schema, the classification is in "structured_output".
        # Without it, it's in "result".
        raw = envelope.get("structured_output") or envelope.get("result", result.stdout)
        logger.debug("Raw classification result: %s", raw[:2000] if isinstance(raw, str) else raw)
        if isinstance(raw, str):
            data = _parse_json_response(raw)
        else:
            data = raw

        return Classification(
            title=data.get("title", ""),
            tags=data.get("tags", []),
            correspondent=data.get("correspondent", ""),
            document_type=data.get("document_type", ""),
            confidence=data.get("confidence", "low"),
            reasoning=data.get("reasoning", ""),
        )


def _parse_json_response(raw: str) -> dict:
    # Try direct parse first
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Try extracting JSON from markdown code fences
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding first { ... } block
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise ClassificationError(f"Failed to parse classification JSON: {raw[:500]}")
