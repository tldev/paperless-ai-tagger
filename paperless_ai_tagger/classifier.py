import json
import logging
import shutil
import subprocess

from paperless_ai_tagger.models import Classification
from paperless_ai_tagger.prompt import CLASSIFICATION_SCHEMA, build_prompt

logger = logging.getLogger(__name__)


class ClassificationError(Exception):
    pass


class Classifier:
    def __init__(self, model: str = "sonnet"):
        self.model = model
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
            "--no-session-persistence",
        ]

        logger.debug("Running claude CLI with model=%s", self.model)

        try:
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except subprocess.TimeoutExpired:
            raise ClassificationError("claude CLI timed out after 120 seconds")

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

        # The --output-format json wraps the result in an envelope.
        # The actual classification is in the "result" field.
        raw = envelope.get("result", result.stdout)
        if isinstance(raw, str):
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                raise ClassificationError(f"Failed to parse classification JSON: {raw[:500]}")
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
