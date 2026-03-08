FROM python:3.12-slim

# Install Node.js for npm-based MCP servers
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install all provider SDKs and common deps up front
RUN pip install --no-cache-dir \
    anthropic \
    openai \
    google-genai \
    httpx \
    pydantic

WORKDIR /workspace

ENTRYPOINT ["python", "/app/entrypoint.py"]
