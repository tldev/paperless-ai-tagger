# paperless-ai-tagger

Automatically classify, tag, and title [Paperless-ngx](https://docs.paperless-ngx.com/) documents using the [Claude CLI](https://docs.anthropic.com/en/docs/claude-code).

Given a document's OCR text, paperless-ai-tagger uses Claude to generate a descriptive title, assign tags, identify the correspondent, and set the document type. It prefers your existing taxonomy and only creates new entries when nothing fits.

## Features

- Classifies documents by title, tags, correspondent, and document type
- Merge or overwrite mode for existing metadata
- Idempotent: marks processed documents with a tag to avoid reprocessing
- Watch mode for continuous polling
- Dry-run mode to preview changes
- Configurable entirely through environment variables
- Docker image for easy deployment

## Requirements

- Paperless-ngx instance with API access
- Claude CLI authenticated via OAuth token (uses your existing Claude subscription)

## Authentication

Generate an OAuth token for headless use:

```bash
claude setup-token
```

This produces a token (starting with `sk-ant-oat01-`) valid for one year. Set it as `CLAUDE_CODE_OAUTH_TOKEN` in your environment.

## Install

### Docker Compose (recommended)

```yaml
services:
  paperless-ai-tagger:
    image: ghcr.io/tldev/paperless-ai-tagger:latest
    environment:
      PAPERLESS_URL: http://paperless:8000
      PAPERLESS_API_TOKEN: your-api-token-here
      CLAUDE_CODE_OAUTH_TOKEN: your-claude-oauth-token-here
      CLAUDE_MODEL: sonnet
      MODE: merge
      POLL_INTERVAL: 300
      LOG_LEVEL: info
    restart: unless-stopped
```

### pip

```bash
pip install paperless-ai-tagger
```

## Configuration

All settings are configured via environment variables.

| Variable | Default | Description |
|---|---|---|
| `PAPERLESS_URL` | (required) | Base URL of your Paperless-ngx instance |
| `PAPERLESS_API_TOKEN` | (required) | Paperless-ngx API token |
| `CLAUDE_CODE_OAUTH_TOKEN` | (required) | Claude CLI OAuth token |
| `CLAUDE_MODEL` | `sonnet` | Claude model to use |
| `PROCESSED_TAG` | `processed-by-ai` | Tag name used to mark processed documents |
| `MODE` | `merge` | `merge` keeps existing metadata, `overwrite` replaces it |
| `POLL_INTERVAL` | `300` | Seconds between polls in watch mode |
| `BATCH_SIZE` | `10` | Documents to process per batch |
| `BATCH_DELAY` | `5` | Seconds to wait between documents |
| `DRY_RUN` | `false` | Preview changes without applying them |
| `LOG_LEVEL` | `info` | Logging level (`debug`, `info`, `warning`, `error`) |
| `CLASSIFY_TITLE` | `true` | Whether to classify document titles |
| `CLASSIFY_TAGS` | `true` | Whether to classify tags |
| `CLASSIFY_CORRESPONDENT` | `true` | Whether to classify correspondents |
| `CLASSIFY_DOCUMENT_TYPE` | `true` | Whether to classify document types |
| `CUSTOM_PROMPT` | (empty) | Additional instructions appended to the classification prompt |
| `MAX_CONTENT_LENGTH` | `50000` | Max characters of document content sent to Claude |

## Usage

### Process documents

```bash
# Process all untagged documents
paperless-ai-tagger process

# Process a single document
paperless-ai-tagger process --document-id 42

# Preview changes without applying
paperless-ai-tagger process --dry-run

# Continuously watch for new documents
paperless-ai-tagger process --watch

# Limit batch size
paperless-ai-tagger process --limit 5
```

### Inspect taxonomy

```bash
paperless-ai-tagger list-tags
paperless-ai-tagger list-correspondents
paperless-ai-tagger list-types
```

### Modes

**Merge** (default): New tags are added alongside existing ones. Title, correspondent, and document type are only set if currently empty (or the title looks auto-generated).

In merge mode, a title is considered auto-generated if it matches any of these conditions:
- Contains a file extension (`.pdf`, `.jpg`, `.tiff`, etc.)
- Starts with a scanner/camera prefix (`scan_`, `Scan `, `IMG_`)
- Is a generic placeholder (`document`, `untitled`, `attachment`, `download`)
- Matches the original filename from Paperless (with or without extension, ignoring case and separator differences)

**Overwrite**: All classified fields are replaced with the AI's suggestion. Existing tags are replaced, not merged.

## Development

```bash
git clone https://github.com/tldev/paperless-ai-tagger.git
cd paperless-ai-tagger
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Run tests

```bash
pytest -v
```

### Lint and format

```bash
ruff check .
ruff format .
```

### Project structure

```
paperless_ai_tagger/
  __init__.py       - Version
  __main__.py       - Entry point
  cli.py            - Click CLI commands
  config.py         - Settings via environment variables
  client.py         - Paperless-ngx API client
  classifier.py     - Claude CLI wrapper
  processor.py      - Document processing logic
  prompt.py         - Classification prompt and schema
  models.py         - Data models
```

## License

MIT
