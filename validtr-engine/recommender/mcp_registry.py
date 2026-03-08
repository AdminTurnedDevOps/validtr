"""MCP Registry lookup for discovering available MCP servers."""

import logging

import httpx

logger = logging.getLogger(__name__)

# Curated registry of well-known MCP servers with tags for relevance matching
CURATED_MCP_SERVERS = [
    # --- File & Code ---
    {
        "name": "filesystem",
        "description": "Read, write, move, and search files on the local filesystem",
        "transport": "stdio",
        "install": "npx -y @modelcontextprotocol/server-filesystem",
        "credentials": "none",
        "capabilities": ["file-read", "file-write", "directory-listing", "file-search"],
        "tags": ["code", "files", "development"],
    },
    {
        "name": "git",
        "description": "Git operations — clone, diff, log, branch, commit",
        "transport": "stdio",
        "install": "npx -y @modelcontextprotocol/server-git",
        "credentials": "none",
        "capabilities": ["version-control", "git-operations", "diff", "commit"],
        "tags": ["code", "development", "version-control"],
    },
    {
        "name": "github",
        "description": "GitHub API — repos, issues, PRs, code search, actions",
        "transport": "stdio",
        "install": "npx -y @modelcontextprotocol/server-github",
        "credentials": "GITHUB_TOKEN",
        "capabilities": ["repo-management", "issue-tracking", "pr-management", "code-search"],
        "tags": ["code", "development", "github", "ci-cd"],
    },
    # --- Web & HTTP ---
    {
        "name": "fetch",
        "description": "Fetch web pages, REST APIs, and documentation — read content from URLs",
        "transport": "stdio",
        "install": "npx -y @modelcontextprotocol/server-fetch",
        "credentials": "none",
        "capabilities": ["web-fetch", "url-reading", "api-access", "documentation-lookup"],
        "tags": ["web", "http", "api", "documentation", "research", "rest"],
    },
    {
        "name": "puppeteer",
        "description": "Browser automation — navigate, click, fill forms, screenshot, scrape rendered pages",
        "transport": "stdio",
        "install": "npx -y @modelcontextprotocol/server-puppeteer",
        "credentials": "none",
        "capabilities": ["web-scraping", "browser-automation", "screenshot", "form-filling", "e2e-testing"],
        "tags": ["web", "browser", "testing", "scraping", "automation", "frontend"],
    },
    {
        "name": "firecrawl",
        "description": "Advanced web scraping and structured data extraction from websites",
        "transport": "stdio",
        "install": "npx -y firecrawl-mcp",
        "credentials": "FIRECRAWL_API_KEY",
        "capabilities": ["web-scraping", "data-extraction", "structured-data"],
        "tags": ["web", "scraping", "data", "extraction"],
    },
    # --- Search ---
    {
        "name": "brave-search",
        "description": "Web search via Brave — find documentation, examples, best practices",
        "transport": "stdio",
        "install": "npx -y @modelcontextprotocol/server-brave-search",
        "credentials": "BRAVE_API_KEY",
        "capabilities": ["web-search", "information-retrieval"],
        "tags": ["search", "web", "research", "documentation"],
    },
    {
        "name": "exa",
        "description": "AI-native semantic search — find similar content, deep research",
        "transport": "stdio",
        "install": "npx -y exa-mcp-server",
        "credentials": "EXA_API_KEY",
        "capabilities": ["semantic-search", "research", "similar-content"],
        "tags": ["search", "research", "ai", "semantic"],
    },
    # --- Databases ---
    {
        "name": "postgres",
        "description": "PostgreSQL — SQL queries, schema inspection, CRUD operations",
        "transport": "stdio",
        "install": "npx -y @modelcontextprotocol/server-postgres",
        "credentials": "DATABASE_URL",
        "capabilities": ["sql-query", "schema-inspection", "data-management", "database"],
        "tags": ["database", "postgres", "sql", "backend", "data"],
    },
    {
        "name": "sqlite",
        "description": "SQLite — create, query, and manage local databases",
        "transport": "stdio",
        "install": "npx -y @anthropics/mcp-server-sqlite",
        "credentials": "none",
        "capabilities": ["sql-query", "database", "local-storage"],
        "tags": ["database", "sqlite", "sql", "local", "backend"],
    },
    {
        "name": "mongodb",
        "description": "MongoDB — CRUD, aggregation pipelines, schema inspection",
        "transport": "stdio",
        "install": "npx -y mongodb-mcp-server",
        "credentials": "MONGODB_URI",
        "capabilities": ["nosql", "document-database", "aggregation"],
        "tags": ["database", "mongodb", "nosql", "backend"],
    },
    {
        "name": "redis",
        "description": "Redis — key-value store, caching, pub-sub, sessions",
        "transport": "stdio",
        "install": "npx -y redis-mcp-server",
        "credentials": "REDIS_URL",
        "capabilities": ["caching", "key-value", "pub-sub", "sessions"],
        "tags": ["database", "redis", "caching", "backend", "sessions"],
    },
    # --- Cloud & Infrastructure ---
    {
        "name": "cloudflare",
        "description": "Cloudflare Workers, KV, R2, D1 — deploy and manage edge infrastructure",
        "transport": "stdio",
        "install": "npx -y @anthropics/mcp-server-cloudflare",
        "credentials": "CLOUDFLARE_API_TOKEN",
        "capabilities": ["edge-deployment", "kv-storage", "r2-storage", "workers"],
        "tags": ["cloud", "infrastructure", "deployment", "edge", "serverless"],
    },
    {
        "name": "aws",
        "description": "AWS services — S3, Lambda, EC2, IAM, CloudFormation",
        "transport": "stdio",
        "install": "npx -y aws-mcp-server",
        "credentials": "AWS_ACCESS_KEY_ID",
        "capabilities": ["cloud-infrastructure", "s3", "lambda", "ec2"],
        "tags": ["cloud", "aws", "infrastructure", "deployment"],
    },
    {
        "name": "kubernetes",
        "description": "Kubernetes — pods, deployments, services, logs, cluster management",
        "transport": "stdio",
        "install": "npx -y kubernetes-mcp-server",
        "credentials": "KUBECONFIG",
        "capabilities": ["container-orchestration", "deployment", "cluster-management"],
        "tags": ["kubernetes", "k8s", "infrastructure", "containers", "devops"],
    },
    {
        "name": "docker",
        "description": "Docker — build images, run containers, manage volumes",
        "transport": "stdio",
        "install": "npx -y docker-mcp-server",
        "credentials": "none",
        "capabilities": ["containers", "image-building", "container-management"],
        "tags": ["docker", "containers", "infrastructure", "devops"],
    },
    # --- AI & Reasoning ---
    {
        "name": "sequential-thinking",
        "description": "Step-by-step reasoning — problem decomposition, architecture planning",
        "transport": "stdio",
        "install": "npx -y @modelcontextprotocol/server-sequential-thinking",
        "credentials": "none",
        "capabilities": ["reasoning", "planning", "decomposition", "architecture"],
        "tags": ["reasoning", "planning", "complex-tasks", "architecture"],
    },
    {
        "name": "memory",
        "description": "Persistent memory via knowledge graph — remember context across steps",
        "transport": "stdio",
        "install": "npx -y @modelcontextprotocol/server-memory",
        "credentials": "none",
        "capabilities": ["knowledge-storage", "entity-relations", "persistent-memory"],
        "tags": ["memory", "context", "knowledge-graph"],
    },
    # --- Communication & Project ---
    {
        "name": "slack",
        "description": "Slack — send messages, read channels, manage conversations",
        "transport": "stdio",
        "install": "npx -y @anthropics/mcp-server-slack",
        "credentials": "SLACK_TOKEN",
        "capabilities": ["messaging", "channels", "notifications"],
        "tags": ["communication", "slack", "messaging"],
    },
    {
        "name": "linear",
        "description": "Linear — issues, projects, sprints, roadmaps",
        "transport": "stdio",
        "install": "npx -y linear-mcp-server",
        "credentials": "LINEAR_API_KEY",
        "capabilities": ["issue-tracking", "project-management", "sprint-management"],
        "tags": ["project-management", "issues", "agile"],
    },
    {
        "name": "notion",
        "description": "Notion — search, read, create pages and databases",
        "transport": "stdio",
        "install": "npx -y @notionhq/mcp-server-notion",
        "credentials": "NOTION_API_KEY",
        "capabilities": ["documentation", "wiki", "database", "content-management"],
        "tags": ["documentation", "wiki", "knowledge-base"],
    },
    # --- Security & Auth ---
    {
        "name": "auth0",
        "description": "Auth0 — manage authentication flows, users, applications, OAuth/JWT",
        "transport": "stdio",
        "install": "npx -y auth0-mcp-server",
        "credentials": "AUTH0_DOMAIN",
        "capabilities": ["authentication", "authorization", "user-management", "oauth", "jwt"],
        "tags": ["auth", "security", "identity", "oauth", "jwt", "web"],
    },
    # --- Code Execution & Testing ---
    {
        "name": "e2b",
        "description": "E2B — secure cloud sandboxes for code execution and testing",
        "transport": "stdio",
        "install": "npx -y e2b-mcp-server",
        "credentials": "E2B_API_KEY",
        "capabilities": ["code-execution", "sandbox", "testing", "prototyping"],
        "tags": ["execution", "sandbox", "testing", "code"],
    },
    {
        "name": "browserstack",
        "description": "BrowserStack — cross-browser testing, real device testing",
        "transport": "stdio",
        "install": "npx -y browserstack-mcp-server",
        "credentials": "BROWSERSTACK_KEY",
        "capabilities": ["cross-browser-testing", "device-testing"],
        "tags": ["testing", "browser", "qa"],
    },
    # --- API & Integration ---
    {
        "name": "openapi",
        "description": "OpenAPI spec validation, API exploration, client generation",
        "transport": "stdio",
        "install": "npx -y openapi-mcp-server",
        "credentials": "none",
        "capabilities": ["api-validation", "spec-exploration", "client-generation"],
        "tags": ["api", "openapi", "rest", "swagger", "web"],
    },
    # --- Deployment ---
    {
        "name": "netlify",
        "description": "Netlify — deploy websites, manage DNS, serverless functions",
        "transport": "stdio",
        "install": "npx -y netlify-mcp-server",
        "credentials": "NETLIFY_AUTH_TOKEN",
        "capabilities": ["deployment", "hosting", "serverless"],
        "tags": ["deployment", "hosting", "web", "ci-cd"],
    },
    {
        "name": "vercel",
        "description": "Vercel — deploy frontend apps, serverless functions",
        "transport": "stdio",
        "install": "npx -y vercel-mcp-server",
        "credentials": "VERCEL_TOKEN",
        "capabilities": ["deployment", "hosting", "serverless", "frontend"],
        "tags": ["deployment", "hosting", "web", "frontend"],
    },
    # --- Monitoring ---
    {
        "name": "grafana",
        "description": "Grafana — dashboards, datasources, alerts, metrics",
        "transport": "stdio",
        "install": "npx -y grafana-mcp-server",
        "credentials": "GRAFANA_API_KEY",
        "capabilities": ["monitoring", "dashboards", "metrics", "alerting"],
        "tags": ["monitoring", "observability", "metrics"],
    },
]


class MCPRegistryClient:
    """Queries MCP registries to discover available servers."""

    def __init__(self):
        self.curated = CURATED_MCP_SERVERS

    async def search(self, query: str, capabilities: list[str] | None = None) -> list[dict]:
        """Search for MCP servers matching the query and required capabilities."""
        results = await self._search_online(query)
        if not results:
            results = self._search_curated(query, capabilities)
        return results

    async def _search_online(self, query: str) -> list[dict]:
        """Search Smithery or mcp.so for MCP servers."""
        for base_url in [
            "https://registry.smithery.ai/api/v1/servers",
            "https://registry.mcp.so/api/servers",
        ]:
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    response = await client.get(base_url, params={"q": query, "limit": 10})
                    if response.status_code == 200:
                        data = response.json()
                        servers = data if isinstance(data, list) else data.get("servers", data.get("results", []))
                        if servers:
                            return [
                                {
                                    "name": s.get("name", s.get("qualifiedName", "")),
                                    "description": s.get("description", ""),
                                    "transport": s.get("transport", "stdio"),
                                    "install": s.get("install_command", s.get("installCommand", f"npx -y {s.get('name', '')}")),
                                    "credentials": s.get("credentials", "none"),
                                    "capabilities": s.get("capabilities", s.get("tools", [])),
                                    "source": base_url.split("/")[2],
                                }
                                for s in servers
                            ]
            except (httpx.HTTPError, Exception) as e:
                logger.debug("Online registry %s failed: %s", base_url, e)
        return []

    def _search_curated(
        self, query: str, capabilities: list[str] | None = None
    ) -> list[dict]:
        """Search curated registry with word-level fuzzy matching."""
        query_words = set(query.lower().split())
        results = []

        for server in self.curated:
            score = 0
            name_lower = server["name"].lower()
            desc_lower = server["description"].lower()
            server_tags = set(server.get("tags", []))

            # Name match (strongest signal)
            if any(w in name_lower for w in query_words):
                score += 5
            # Tag match
            score += len(query_words & server_tags) * 3
            # Description word match
            for w in query_words:
                if len(w) >= 3 and w in desc_lower:
                    score += 2
            # Capability match
            for cap in server["capabilities"]:
                if any(w in cap for w in query_words):
                    score += 1
            # Required capabilities overlap
            if capabilities:
                cap_overlap = set(server["capabilities"]) & set(capabilities)
                score += len(cap_overlap) * 2

            if score > 0:
                results.append({**server, "source": "curated", "_score": score})

        results.sort(key=lambda x: x["_score"], reverse=True)
        return [{k: v for k, v in r.items() if k != "_score"} for r in results[:10]]

    def get_all(self) -> list[dict]:
        """Return all curated servers for the LLM to reason over."""
        return [{**s, "source": "curated"} for s in self.curated]
