FROM python:3.12-slim AS base

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Install Node.js (required for Claude CLI)
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install Claude CLI
RUN npm install -g @anthropic-ai/claude-code

WORKDIR /app

COPY pyproject.toml README.md .
COPY paperless_ai_tagger/ paperless_ai_tagger/

RUN pip install --no-cache-dir .

ENTRYPOINT ["paperless-ai-tagger"]
CMD ["process", "--watch"]
