# Architecture decisions

One short record per decision that shapes the code and isn't obvious from it. Each
says what was decided and why; how it works lives in the linked architecture page.

| ADR | Decision |
|---|---|
| [001](ADR-001.md) | PokéAPI data is ingested offline, never called at runtime |
| [002](ADR-002.md) | One tool-planning agent; the LLM picks tools, no routes |
| [003](ADR-003.md) | Closed-form answers are written by code; the LLM only narrates evidence |
| [004](ADR-004.md) | Writes are gated in code, not in prompts |
| [005](ADR-005.md) | Every LLM feature works keyless, on a fixed call budget |
| [006](ADR-006.md) | One damage formula in TypeScript, ported to Python and fixture-checked |
| [007](ADR-007.md) | The team summary is written in the background; grades stay deterministic |
| [008](ADR-008.md) | Team and calc scopes get a smaller tool set to fit the planning prompt |
| [009](ADR-009.md) | Rules every client must agree on (grades, type chart) live on the backend |

**Adding one:** next number, the same four headings (Status · Context · Decision ·
Consequences), a row above, and a link from the component manifest it affects
(`docs/components/*.yaml`). Superseding a decision: write a new ADR and set the old
one's status to `Superseded by ADR-NNN` — don't rewrite history.

Older decisions are also recorded in `openspec/changes/archive/`.
