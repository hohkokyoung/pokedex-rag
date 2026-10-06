# pokérag docs

| Section | For | Pages |
|---|---|---|
| **product/** | what each page of the site does | [home](product/home.md) · [pokedex](product/pokedex.md) · [ask](product/ask.md) · [teams](product/teams.md) |
| **architecture/** | how it works and why | [overview](architecture/overview.md) · [ask-agent](architecture/ask-agent.md) · [retrieval](architecture/retrieval.md) · [team-coach](architecture/team-coach.md) · [damage-calc](architecture/damage-calc.md) |
| **guides/** | how to do things | [local-dev](guides/local-dev.md) · [data-pipeline](guides/data-pipeline.md) · [eval](guides/eval.md) |

Elsewhere:

- **`openspec/specs/`** — what the system promises (SHALL rules + scenarios). If a doc
  and a spec disagree, the spec is the intended behaviour.
- **`openspec/changes/`** — work in progress; **`archive/`** — past decisions.
- **`CLAUDE.md`** — conventions and gotchas for contributors and coding agents.

## Keeping these current

Each fact has one home; other pages link to it rather than copy it. When behaviour
described here changes, update the page in the same commit. OpenSpec changes end with a
docs task and check for drift before archiving (`openspec/config.yaml`).
