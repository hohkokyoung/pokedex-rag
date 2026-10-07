# Ask (`/ask`)

"Ask the Pokédex" — natural-language questions answered only from the app's data.
Every answer cites the records it came from; if the data can't answer, it says so
instead of guessing.

## What you can ask

| Kind | Example |
|---|---|
| Rankings and filters | "Fastest non-legendary Fire types", "Highest Attack in Gen 4" |
| One Pokémon | "Tell me about Snorlax" |
| Moves and learnsets | "Can Pikachu learn Surf in Scarlet?", "Which Fire types learn Will-O-Wisp?" |
| Moves, abilities, items | "What does Earthquake do?", "What does Leftovers do?" |
| Types and matchups | "What is Fire weak to?", "A special attacker that covers Dark" |
| Look-alikes | "Pokémon like Jigglypuff" |
| Lore | "Fire types that live near volcanoes" |
| Where to catch | "Where can I catch Pikachu?" |
| For you | "Recommend a Pokémon for me" (uses your favourites and preferred types) |
| Several at once | "Which moves beat Garchomp, and what is Fire weak to?" |

## Reading an answer

- **Plan strip** — how many steps, who planned them (**keywords** or the **LLM**),
  whether it was cached, the time taken and the number of LLM calls. Expand it to see
  each step and what it found.
- **Verdict** — one direct sentence first, then bullets if there's a list. `[n]`
  marks link to the sources.
- **Evidence** — the typed results drawn as tables, charts and cards (rankings, type
  charts, learnsets, learner lists, Pokémon cards).
- **Sources** — the numbered records behind the citations.
- **Notice** — if part of the question couldn't be applied ("cute"), the answer says
  so up front.
- **Follow-ups** — suggested next questions.

## Your profile

A drawer for **preferred types** and your **favourites** (set with ♡ on detail pages).
They only affect "for you" questions. Single-user and local — nothing leaves your
machine except LLM calls, if a key is set.

## Without an LLM key

Still works: questions are planned by keywords; rankings, learn checks, move info and
type charts are written by code; other answers quote the most relevant records
directly ("add an LLM key for narrated answers").

How it works: [../architecture/ask-agent.md](../architecture/ask-agent.md).

Code: [ask-agent manifest](../components/ask-agent.yaml). Streaming state lives in
`components/agent/useAsk.ts`.
