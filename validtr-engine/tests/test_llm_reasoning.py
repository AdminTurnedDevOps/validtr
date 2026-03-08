"""Tests for LLM reasoning helper functions."""

from recommender.llm_reasoning import _parse_skills


def test_parse_skills_filters_to_catalog():
    available = [
        {"name": "jwt-token-validation", "source": "anthropic"},
        {"name": "fastapi-routing", "source": "github-copilot"},
    ]
    raw = [
        {"name": "jwt-token-validation", "source": "anthropic"},
        {"name": "totally-made-up-skill", "source": "anthropic"},
        "fastapi-routing (github-copilot)",
        "another-fake-skill",
    ]

    parsed = _parse_skills(raw_skills=raw, available_skills=available)

    assert parsed == [
        "jwt-token-validation (anthropic)",
        "fastapi-routing (github-copilot)",
    ]


def test_parse_skills_rejects_ambiguous_name_without_source():
    available = [
        {"name": "shared-skill", "source": "anthropic"},
        {"name": "shared-skill", "source": "github-copilot"},
    ]
    raw = ["shared-skill"]

    parsed = _parse_skills(raw_skills=raw, available_skills=available)

    assert parsed == []


def test_parse_skills_returns_empty_when_catalog_missing():
    raw = [
        {"name": "jwt-token-validation", "source": "anthropic"},
        "fastapi-routing (github-copilot)",
    ]

    parsed = _parse_skills(raw_skills=raw, available_skills=[])

    assert parsed == []
