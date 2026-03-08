"""Skills Registry — fetches agent skills from upstream GitHub catalogs at runtime.

Sources:
  - https://github.com/anthropics/skills
  - https://github.com/github/awesome-copilot

Skills are fetched on first use, cached for 1 hour. No local curation needed.
"""

import asyncio
import logging
import time

import httpx
import yaml

logger = logging.getLogger(__name__)

CATALOGS = [
    {
        "owner": "anthropics",
        "repo": "skills",
        "skills_path": "skills",
        "source": "anthropic",
    },
    {
        "owner": "github",
        "repo": "awesome-copilot",
        "skills_path": "skills",
        "source": "github-copilot",
    },
]

# Cache TTL in seconds (1 hour)
_CACHE_TTL = 3600

# Max concurrent requests to GitHub to avoid rate limits
_MAX_CONCURRENT = 20


class SkillsRegistryClient:
    """Fetches and caches agent skills from upstream GitHub catalogs."""

    def __init__(self):
        self._cache: list[dict] | None = None
        self._cache_time: float = 0

    async def get_all(self) -> list[dict]:
        """Return all skills from both catalogs (cached)."""
        now = time.time()
        if self._cache is not None and (now - self._cache_time) < _CACHE_TTL:
            return self._cache

        skills = []
        for catalog in CATALOGS:
            fetched = await self._fetch_catalog(catalog)
            skills.extend(fetched)
            logger.info(
                "Fetched %d skills from %s/%s",
                len(fetched),
                catalog["owner"],
                catalog["repo"],
            )

        self._cache = skills
        self._cache_time = now
        logger.info("Skills registry: %d total skills cached", len(skills))
        return skills

    async def search(self, query: str) -> list[dict]:
        """Search skills by keyword relevance."""
        all_skills = await self.get_all()
        if not query.strip():
            return all_skills

        query_words = set(query.lower().split())
        scored = []

        for skill in all_skills:
            score = 0
            name_lower = skill["name"].lower()
            desc_lower = skill["description"].lower()

            if any(w in name_lower for w in query_words):
                score += 5
            for w in query_words:
                if len(w) >= 3 and w in desc_lower:
                    score += 2

            if score > 0:
                scored.append((score, skill))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored[:15]]

    async def _fetch_catalog(self, catalog: dict) -> list[dict]:
        """Fetch all skills from a single GitHub catalog repo."""
        owner = catalog["owner"]
        repo = catalog["repo"]
        skills_path = catalog["skills_path"]
        source = catalog["source"]

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Get the full repo tree in a single API call
                tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1"
                resp = await client.get(
                    tree_url, headers={"Accept": "application/vnd.github+json"}
                )
                if resp.status_code != 200:
                    logger.warning(
                        "GitHub tree API returned %d for %s/%s",
                        resp.status_code,
                        owner,
                        repo,
                    )
                    return []

                tree = resp.json().get("tree", [])

                # Find all SKILL.md files under skills_path/
                skill_paths = [
                    item["path"]
                    for item in tree
                    if item.get("path", "").startswith(f"{skills_path}/")
                    and item["path"].endswith("/SKILL.md")
                    and item.get("type") == "blob"
                ]

                # Fetch all SKILL.md files concurrently with a semaphore
                sem = asyncio.Semaphore(_MAX_CONCURRENT)

                async def _fetch_one(path: str) -> dict | None:
                    async with sem:
                        return await self._fetch_skill_md(
                            client, owner, repo, path, source
                        )

                results = await asyncio.gather(
                    *[_fetch_one(p) for p in skill_paths], return_exceptions=True
                )

                return [r for r in results if isinstance(r, dict)]

        except (httpx.HTTPError, Exception) as e:
            logger.warning("Failed to fetch skills from %s/%s: %s", owner, repo, e)
            return []

    async def _fetch_skill_md(
        self,
        client: httpx.AsyncClient,
        owner: str,
        repo: str,
        path: str,
        source: str,
    ) -> dict | None:
        """Fetch a single SKILL.md and extract name + description from frontmatter."""
        raw_url = (
            f"https://raw.githubusercontent.com/{owner}/{repo}/main/{path}"
        )
        try:
            resp = await client.get(raw_url)
            if resp.status_code != 200:
                return None

            meta = _parse_frontmatter(resp.text)
            if not meta or not meta.get("name"):
                # Fall back to folder name
                parts = path.split("/")
                folder_name = parts[-2] if len(parts) >= 2 else path
                meta = meta or {}
                meta.setdefault("name", folder_name)

            return {
                "name": meta.get("name", ""),
                "description": meta.get("description", ""),
                "source": source,
                "repo": f"{owner}/{repo}",
                "path": path,
            }
        except (httpx.HTTPError, Exception):
            return None


def _parse_frontmatter(content: str) -> dict | None:
    """Parse YAML frontmatter from a SKILL.md file."""
    content = content.strip()
    if not content.startswith("---"):
        return None

    end = content.find("---", 3)
    if end == -1:
        return None

    frontmatter = content[3:end].strip()
    try:
        return yaml.safe_load(frontmatter)
    except yaml.YAMLError:
        return None
