# Scoring

Current scoring for code tasks uses weighted dimensions:

- Test passing: `40%`
- Execution success: `25%`
- Syntax validity: `15%`
- Completeness (LLM judge): `20%`

## Notes

- Dedicated scorer is implemented for code tasks.
- Other task types currently fall back to code scorer behavior.
