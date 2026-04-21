# Worktree Notes for Parallel Agents

## Recommendation
Yes — use separate git worktrees for these five implementation streams.

Why:
- the main repo is already dirty with legitimate ongoing work
- these tasks touch different subsystems and will merge more cleanly from isolated worktrees
- retrieval, route integration, read APIs, and validation can proceed in parallel with lower conflict risk

## Recommended Split
- Agent A: corpus schema + seed
- Agent B: retrieval service
- Agent C: capture enrichment
- Agent D: session/read APIs
- Agent E: validation and observability

## Baseline Rule
Before spawning more worktrees:
- treat the current tested repo state as the baseline
- do not purge files aggressively unless they are clearly generated junk
- avoid parallel coding directly in the already-dirty main tree

## Integration Order
1. corpus schema/seed
2. retrieval service
3. capture enrichment
4. session/read APIs
5. validation and smoke checks

## Tooling Note
These briefs are written to be tool-agnostic.
They can be handed to:
- Codex agents
- Claude Code
- any other implementation agent working in a separate worktree
