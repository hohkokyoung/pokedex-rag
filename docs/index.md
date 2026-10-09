# pokérag docs

| Section | For | Pages |
|---|---|---|
| **product/** | what each page of the site (and the app) does | [home](product/home.md) · [pokedex](product/pokedex.md) · [ask](product/ask.md) · [teams](product/teams.md) · [mobile app](product/mobile.md) |
| **architecture/** | how it works and why | [overview](architecture/overview.md) · [data](architecture/data.md) · [ask-agent](architecture/ask-agent.md) ([planners](architecture/ask-agent-planners.md), [traces](architecture/ask-agent-traces.md)) · [retrieval](architecture/retrieval.md) · [team-coach](architecture/team-coach.md) · [damage-calc](architecture/damage-calc.md) |
| **guides/** | how to do things | [local-dev](guides/local-dev.md) · [data-pipeline](guides/data-pipeline.md) · [eval](guides/eval.md) · [media](guides/media.md) · [mobile](guides/mobile.md) |
| **components/** | code → docs/specs/decisions index (YAML, for tooling) | [about](components/README.md) · [pokedex](components/pokedex.yaml) · [ask-agent](components/ask-agent.yaml) · [retrieval](components/retrieval.yaml) · [team-coach](components/team-coach.yaml) · [damage-calc](components/damage-calc.yaml) · [data-pipeline](components/data-pipeline.yaml) · [media](components/media.yaml) · [mobile](components/mobile.yaml) |
| **decisions/** | why it's built this way (ADRs) | [all ADRs](decisions/README.md) |

Elsewhere:

- **`openspec/specs/`** — what the system promises (SHALL rules + scenarios). If a doc
  and a spec disagree, the spec is the intended behaviour.
- **`openspec/changes/`** — what is being changed; **`archive/`** — how past changes
  were planned. Decisions that still constrain the code are distilled into `decisions/`.
- **`CLAUDE.md`** — conventions and gotchas for contributors and coding agents.

## Keeping these current

`docs/` is what the system is, `openspec/` is what is being changed, and the code is
what actually exists. Each fact has one home; other pages link to it rather than copy it. When behaviour
described here changes, update the page in the same commit. OpenSpec changes end with a
docs task and check for drift before archiving (`openspec/config.yaml`).
