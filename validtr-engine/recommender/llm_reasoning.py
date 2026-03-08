"""LLM reasoning component of the Recommendation Engine."""

import json
import logging
import re

from models.stack import (
    FrameworkRecommendation,
    LLMRecommendation,
    MCPServerRecommendation,
    MCPTransport,
    StackRecommendation,
)
from models.task import TaskDefinition
from providers.base import LLMProvider, Message
from recommender.prompts import RECOMMENDATION_SYSTEM, RECOMMENDATION_USER

logger = logging.getLogger(__name__)
_SKILL_WITH_SOURCE_PATTERN = re.compile(r"^\s*(?P<name>.+?)\s*\((?P<source>[^()]+)\)\s*$")


class LLMReasoningEngine:
    """Uses an LLM to synthesize search results and registry data into a stack recommendation."""

    def __init__(self, provider: LLMProvider):
        self.provider = provider

    async def recommend(
        self,
        task: TaskDefinition,
        web_results: list[dict],
        mcp_servers: list[dict],
        available_skills: list[dict] | None = None,
        preferred_provider: str | None = None,
    ) -> StackRecommendation:
        """Generate a stack recommendation using LLM reasoning."""
        # Format skills catalog for the prompt — just name, description, source
        skills_text = "No skills available"
        if available_skills:
            skills_summary = [
                {"name": s["name"], "description": s["description"], "source": s["source"]}
                for s in available_skills
            ]
            skills_text = json.dumps(skills_summary, indent=2)

        messages = [
            Message(role="system", content=RECOMMENDATION_SYSTEM),
            Message(
                role="user",
                content=RECOMMENDATION_USER.format(
                    task_definition=task.model_dump_json(indent=2),
                    web_results=json.dumps(web_results, indent=2) if web_results else "No results",
                    mcp_servers=json.dumps(mcp_servers, indent=2) if mcp_servers else "No results",
                    available_skills=skills_text,
                    preferred_provider=preferred_provider or "none (choose the best)",
                ),
            ),
        ]

        response = await self.provider.complete_json(messages=messages, max_tokens=2048)

        raw = response.content.strip()
        # Strip markdown code fences that some models wrap JSON in
        if raw.startswith("```"):
            lines = raw.split("\n")
            lines = lines[1:]  # drop ```json or ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            raw = "\n".join(lines)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse recommendation JSON: %s\nRaw: %s", e, raw[:500])
            raise ValueError(f"LLM returned invalid JSON for recommendation: {e}") from e

        llm_data = data["llm"]
        framework_data = data.get("framework", {})
        mcp_list = data.get("mcp_servers", [])

        return StackRecommendation(
            llm=LLMRecommendation(
                provider=llm_data["provider"],
                model=llm_data["model"],
                reason=llm_data.get("reason", ""),
            ),
            framework=FrameworkRecommendation(
                name=framework_data.get("name"),
                reason=framework_data.get("reason", ""),
            ),
            mcp_servers=[
                MCPServerRecommendation(
                    name=s["name"],
                    transport=MCPTransport(s.get("transport", "stdio")),
                    install=s.get("install", ""),
                    credentials=s.get("credentials", "none"),
                    description=s.get("description", ""),
                )
                for s in mcp_list
            ],
            skills=_parse_skills(
                raw_skills=data.get("skills", []),
                available_skills=available_skills or [],
            ),
            prompt_strategy=data.get(
                "prompt_strategy",
                "Decompose requirements, implement incrementally, validate with tests, then refine.",
            ),
            estimated_tokens=data.get("estimated_tokens", 15000),
            estimated_cost=data.get("estimated_cost", "$0.04"),
        )


def _parse_skills(raw_skills: list, available_skills: list[dict]) -> list[str]:
    """Parse and validate skills from LLM response against available catalog skills.

    Only skills that exist in `available_skills` are returned.
    Returned labels are canonicalized as "name (source)".
    """
    if not available_skills:
        return []

    by_name: dict[str, list[dict]] = {}
    by_name_source: dict[tuple[str, str], dict] = {}
    for skill in available_skills:
        name = (skill.get("name") or "").strip()
        source = (skill.get("source") or "").strip()
        if not name:
            continue

        key_name = name.lower()
        key_source = source.lower()
        by_name.setdefault(key_name, []).append(skill)
        if key_source:
            by_name_source[(key_name, key_source)] = skill

    result: list[str] = []
    seen: set[str] = set()
    for s in raw_skills:
        parsed_name = ""
        parsed_source = ""

        if isinstance(s, dict):
            parsed_name = str(s.get("name", "")).strip()
            parsed_source = str(s.get("source", "")).strip()
        elif isinstance(s, str):
            text = s.strip()
            if not text:
                continue
            match = _SKILL_WITH_SOURCE_PATTERN.match(text)
            if match:
                parsed_name = match.group("name").strip()
                parsed_source = match.group("source").strip()
            else:
                parsed_name = text
        else:
            continue

        if not parsed_name:
            continue

        key_name = parsed_name.lower()
        selected: dict | None = None

        if parsed_source:
            selected = by_name_source.get((key_name, parsed_source.lower()))
            if selected is None:
                logger.info(
                    "Dropping non-catalog skill from model output: %s (%s)",
                    parsed_name,
                    parsed_source,
                )
                continue
        else:
            candidates = by_name.get(key_name, [])
            if len(candidates) == 1:
                selected = candidates[0]
            elif len(candidates) > 1:
                logger.info(
                    "Dropping ambiguous skill from model output (missing source): %s",
                    parsed_name,
                )
                continue
            else:
                logger.info("Dropping non-catalog skill from model output: %s", parsed_name)
                continue

        canonical_name = str(selected.get("name", "")).strip()
        canonical_source = str(selected.get("source", "")).strip()
        if not canonical_name:
            continue

        label = (
            f"{canonical_name} ({canonical_source})"
            if canonical_source
            else canonical_name
        )
        if label not in seen:
            seen.add(label)
            result.append(label)

    return result
