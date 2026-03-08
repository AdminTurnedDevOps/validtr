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

## Start Here

<div class="landing-grid landing-grid-2">
  <a class="landing-card" href="/validtr/getting-started/overview">
    <p class="landing-eyebrow">New User Path</p>
    <h3>Understand validtr</h3>
    <p>Get the high-level architecture and workflow before your first run.</p>
  </a>
  <a class="landing-card" href="/validtr/getting-started/quickstart">
    <p class="landing-eyebrow">Fastest Path</p>
    <h3>Run a Task in Minutes</h3>
    <p>Start engine, run a task, and inspect scored output with retries.</p>
  </a>
  <a class="landing-card" href="/validtr/reference/commands/index">
    <p class="landing-eyebrow">CLI Guide</p>
    <h3>Browse All Commands</h3>
    <p>Detailed docs for <code>run</code>, <code>mcp</code>, <code>config</code>, <code>completion</code>, and <code>help</code>.</p>
  </a>
  <a class="landing-card" href="/validtr/reference/api">
    <p class="landing-eyebrow">Engine API</p>
    <h3>Inspect Contracts</h3>
    <p>See endpoints, payload fields, examples, and error behavior.</p>
  </a>
</div>

## Docs Coverage

<div class="landing-note">
  <p>This site is generated from the current codebase and documents command behavior, API contracts, provider/runtime internals, scoring and retry logic, and development workflows.</p>
</div>
