# Teams (`/teams`, `/teams/[id]`)

Build teams of up to six, see how they rate, test them against each other, and ask a
coach.

## Team list — `/teams`

Every saved team as a card, rated by coverage, defence, speed, roles, sets and roster:

- overall grade and score /100 (scaled down until the team has six different Pokémon);
- an **AI summary** of what the team does (descriptive, no advice);
- its play style (hyper offense, setup offense, balance…) and six strategy axes —
  offense, bulk, speed, setup, stall, support — shown **now** (set moves) and **with
  learnable moves**;
- weak to / resists / "hits hard" type facts;
- the six letter grades and the top things to fix.

**New team** creates one; **Open** goes to the team page; **Delete** removes it.

## Team page — `/teams/[id]`

### Your team

The six slots. Each shows types, role and BST; **Edit** opens the set editor:

- ability, item, nature, EVs and IVs, and up to 4 moves — only legal choices for that
  species (its own learnset, abilities, natures);
- base stats and the item's effect alongside.

### Compare with…

Pick another saved team as the opponent (it's kept in the URL as `?vs=`). Both rosters
sit side by side, and the report adds the matchup: who's favoured, their biggest
threats, what you have no answer to, a suggested lead and plan.

### Team rating

| Part | Shows |
|---|---|
| Rating | grade, score, play style, physical/special lean, biggest gap, AI summary (↻ Regenerate) |
| Grades | Coverage, Defence, Speed, Roles, Sets, Roster |
| How it plays | the six strategy axes, now and with learnable moves |
| Type profile | weak spots, resists, how many of 18 types you hit hard, and your core types |
| Sets | per member: item, ability, moves set. Suggested parts appear in grey italics; **Use suggested** fills only the empty parts |
| Defence | per attacking type: who's weak, who resists, and whether it's covered |
| Fix | one concrete fix per weak grade |

### Coach

"Ask anything about <team>." Examples: "What's my team's biggest weakness?", "Which
type should I add for coverage?", "Give Garchomp its best set", "Draft the rest of my
team — I like sweepers, non-legendary".

- **Set changes** come back as a was → now card. Nothing is saved until you press
  **Apply**; **Revert** restores the old set exactly.
- **Drafts** come back as candidate cards with **Add** / **Replace**.
- **"Add Garchomp"** (a direct command) adds it to the next empty slot and offers
  **Undo**. "Should I add Garchomp?" is treated as a question — you get an Add card
  instead.
- With an opponent picked, the coach also knows the matchup and can play a **duel**.

How it works: [../architecture/team-coach.md](../architecture/team-coach.md).

## Code

Files: [team-coach manifest](../components/team-coach.yaml). The slot editor's
choices (moves, abilities, items, natures) come from the shared builder API in the
[pokedex manifest](../components/pokedex.yaml). Engines and grades:
[team-coach.md](../architecture/team-coach.md).
