# Skills Registry Integration

`SkillsRegistryClient` fetches skills from upstream GitHub repos at runtime.

## Sources

- `anthropics/skills`
- `github/awesome-copilot`

## Discovery Mechanism

- fetches GitHub tree for each repo
- finds `skills/**/SKILL.md`
- parses YAML frontmatter (`name`, `description`)

## Runtime Behavior

- cache TTL: 1 hour
- async fetch with bounded concurrency (`20`)
- results merged into one skill catalog

## Search Behavior

`search(query)` scores by:

- skill name match
- description keyword matches

Returns top 15 scored skills.
