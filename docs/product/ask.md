# Ask (`/ask`)

"Ask the Pokédex" — natural-language questions answered only from the app's data.
Every answer cites the records it came from; if the data can't answer, it says so
instead of guessing.

## What you can ask

| Kind | Example |
|---|---|
| Rankings and filters | "Fastest non-legendary Fire types", "Highest Attack in Gen 4" |
| One Pokémon | "Tell me about Snorlax" |
| Moves and learnsets | "Can Pikachu learn Surf in Scarlet?", "Does Garchomp learn Crunch below lvl 30?", "Which Fire types learn Will-O-Wisp?" |
| Moves, abilities, items | "What does Earthquake do?", "What does Leftovers do?" |
| Types and matchups | "What is Fire weak to?", "A special attacker that covers Dark" |
| Look-alikes | "Pokémon like Jigglypuff" |
| Lore | "Fire types that live near volcanoes" |
| Where to catch | "Where can I catch Pikachu?" |
| For you | "Recommend a Pokémon for me" (uses your favourites and preferred types) |
| Several at once | "Which moves beat Garchomp, and what is Fire weak to?" |

## Reading an answer

The answer is laid out as tiles:

- **Answer** — one direct sentence first, then bullets if there's a list. A question
  with several parts gets one row per part ("1 · Which Fire types learn Will-O-Wisp?
  → 75 · 15 by level-up, 60 by TM"). The small numbers are citations: hover to light up
  where the record is drawn, click to read the record itself ("Show in results" scrolls
  to it).
- **How it was answered** — a quiet line at the bottom of the answer tile: who planned
  it (**keywords** or the **LLM**, or cached), the time taken and the LLM calls. Click
  "N lookups" to see each step and what it found. While working, it shows the step
  that's running.
- **Matchups** — a type chart is a card beside the answer, drawn like the home page's
  Type calculator. Long answers show their first 4 bullets ("Show N more") so the two
  cards stay level; after a one-sentence answer the matchups sit underneath as a strip.
- **Evidence tiles** — one per other result: learner lists and Pokémon lists as
  Pokédex cards (with how each one learns the move), rankings, move info, learnsets.
- **Records** — cited records no tile draws (Pokédex entries, descriptions); the rest
  are behind "Show N more".
- **Sources** — every tile ends with the records it came from ("From the Fire type
  chart [11]").
- **Notice** — if part of the question couldn't be applied ("cute"), the answer says
  so up front.
- **Ask next** — once answered, follow-up questions replace the examples in the search
  card.

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
