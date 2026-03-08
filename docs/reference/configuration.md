# Configuration

Local config file:

```text
~/.validtr/config.yaml
```

Example:

```yaml
provider: anthropic
score_threshold: 95.0
max_retries: 3
timeout: 300
engine_addr: "http://127.0.0.1:4041"
```

API keys are environment variables:

```bash
export ANTHROPIC_API_KEY="..."
export OPENAI_API_KEY="..."
export GOOGLE_API_KEY="..."
export TAVILY_API_KEY="..."
```
