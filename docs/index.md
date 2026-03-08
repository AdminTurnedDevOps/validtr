---
layout: home

hero:
  name: validtr docs
  text: Agentic stack validation, end to end
  tagline: Natural language in. Production-grade stack out.
  image:
    src: /validtr-logo.png
    alt: validtr logo
  actions:
    - theme: brand
      text: Get Started
      link: /getting-started/overview
    - theme: alt
      text: CLI Reference
      link: /reference/cli

features:
  - title: Stack Recommendation
    details: Recommends LLM, framework, MCP servers, and skills for each task.
  - title: Containerized Execution
    details: Runs agent workflows in isolated Docker environments.
  - title: Test + Score + Retry
    details: Generates tests, computes score, and iterates until threshold or retry limit.
---

## Documentation Coverage

This docs site is generated from the current codebase and includes:

- CLI commands, flags, and runtime behavior
- Engine API contracts and error handling
- Provider abstraction and model defaults
- Recommendation, MCP registry, and skills registry internals
- Docker execution, generated agent loop behavior, and safety guards
- Test generation, scoring, retry strategy, and current limitations
