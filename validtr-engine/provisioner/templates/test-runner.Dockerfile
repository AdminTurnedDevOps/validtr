FROM python:3.12-slim

WORKDIR /workspace

# Install test dependencies
RUN pip install --no-cache-dir pytest pytest-asyncio httpx requests

# Tests and artifacts are mounted at runtime
CMD ["pytest", "/workspace/tests/", "-v", "--tb=short", "--no-header", "-q"]
