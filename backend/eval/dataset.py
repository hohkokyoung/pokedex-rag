"""Labeled evaluation set for the Pokédex RAG system.

Each case names the tools a correct retrieval plan must include (``expect_tools``:
a tool name, or ``a|b`` alternatives, plus the arguments that matter) and, where
checkable without an LLM, the Pokémon that should appear in the evidence.
``expected_substrings`` and ``abstain`` are graded only with an API key (they need
a generated answer). ``fast_path`` says whether the keyword planner should be
confident enough to skip the LLM planner. ``personalized`` cases run against a
temporary profile set by the harness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Category = Literal[
    "structured", "semantic", "hybrid", "personalized", "refusal", "move", "matchup",
    "learnset", "lookup", "multi",
]


@dataclass
class ToolExpect:
    tool: str  # "get_pokemon" or alternatives "get_pokemon|semantic_search"
    args: dict = field(default_factory=dict)  # only the args that matter


def T(tool: str, **args) -> ToolExpect:  # noqa: N802 — reads like the plan it describes
    return ToolExpect(tool, args)


@dataclass
class EvalCase:
    id: str
    question: str
    category: Category
    expect_tools: list[ToolExpect] = field(default_factory=list)
    multi_part: bool = False
    fast_path: bool | None = None  # None = don't care
    # Any of these dex numbers appearing in the evidence counts as a hit.
    expected_dex_any: list[int] = field(default_factory=list)
    # Exact top-1 Pokémon in the evidence (for ranking questions).
    expected_top1: str | None = None
    # Substrings the answer should contain (LLM grading only).
    expected_substrings: list[str] = field(default_factory=list)
    # Whether the assistant should abstain (LLM grading only).
    abstain: bool = False


DESCRIBE = "get_pokemon|semantic_search"

CASES: list[EvalCase] = [
    # ---------------- structured ----------------
    EvalCase("s1", "Which Pokémon has the highest Attack?", "structured",
             [T("query_pokemon", sort_by="attack", order="desc")], fast_path=True,
             expected_top1="Kartana", expected_substrings=["Kartana"]),
    EvalCase("s2", "Which Pokémon have Speed above 130?", "structured",
             [T("query_pokemon", stat_filters=[{"stat": "speed", "op": "gt", "value": 130}])]),
    EvalCase("s3", "What is the strongest Water-type Pokémon?", "structured",
             [T("query_pokemon", types_all=["water"])]),
    EvalCase("s4", "Which Pokémon has the lowest base stat total?", "structured",
             [T("query_pokemon", sort_by="base_stat_total", order="asc")], fast_path=True),
    EvalCase("s5", "Top 5 Pokémon by base stat total", "structured",
             [T("query_pokemon", sort_by="base_stat_total")]),

    # ---------------- semantic ----------------
    EvalCase("m1", "Tell me about Bulbasaur.", "semantic", [T("get_pokemon", name="Bulbasaur")],
             fast_path=True, expected_dex_any=[1], expected_substrings=["Bulbasaur"]),
    EvalCase("m2", "What is Mewtwo's origin?", "semantic", [T(DESCRIBE)],
             expected_dex_any=[150], expected_substrings=["Mewtwo"]),
    EvalCase("m3", "Describe Snorlax.", "semantic", [T("get_pokemon", name="Snorlax")],
             fast_path=True, expected_dex_any=[143]),
    EvalCase("m4", "What does Gengar look like?", "semantic", [T(DESCRIBE)],
             expected_dex_any=[94]),
    EvalCase("m5", "What is Pikachu known for?", "semantic", [T(DESCRIBE)],
             expected_dex_any=[25]),

    # ---------------- hybrid ----------------
    EvalCase("h1", "Which Fire-type Pokémon live near volcanoes?", "hybrid",
             [T("semantic_search")], expected_dex_any=[126, 219, 323, 4, 5, 6]),
    EvalCase("h2", "What is the strongest Dragon-type and where does it live?", "hybrid",
             [T("query_pokemon", types_all=["dragon"])]),
    EvalCase("h3", "Which Grass-type Pokémon are based on plants or seeds?", "hybrid",
             [T("semantic_search")], expected_dex_any=[1, 2, 3, 43, 44, 45]),

    # ---------------- personalized ----------------
    EvalCase("p1", "Which Pokémon would I probably like?", "personalized", [T("user_profile")],
             fast_path=True),
    EvalCase("p2", "Recommend a Pokémon for me.", "personalized", [T("user_profile")],
             fast_path=True),

    # ---------------- moves, learnsets, matchups, lookups ----------------
    EvalCase("v1", "What does Earthquake do?", "move", [T("move_info", name="Earthquake")],
             fast_path=True),
    EvalCase("v2", "Who learns Earthquake?", "learnset", [T("learnset", move="Earthquake")],
             fast_path=True),
    EvalCase("v3", "Can Garchomp learn Earthquake?", "learnset",
             [T("learnset", pokemon="Garchomp", move="Earthquake")], fast_path=True,
             expected_substrings=["Garchomp"]),
    EvalCase("v4", "Tell me about Psychic", "move",
             [T("move_info", name="Psychic"), T("type_matchup", types=["psychic"])],
             fast_path=False),
    EvalCase("v5", "Which non-legendary Pokémon learn Earthquake?", "learnset",
             [T("learnset", move="Earthquake", legendary=False)], fast_path=False),
    EvalCase("x1", "What is Fire weak to?", "matchup", [T("type_matchup", types=["fire"])],
             fast_path=True),
    EvalCase("x2", "Moves that beat Garchomp", "matchup",
             [T("coverage_vs_types", want="moves")]),
    EvalCase("x3", "A special attacker with coverage against Water and Dark", "matchup",
             [T("coverage_vs_types", attacker_class="special")]),
    EvalCase("l1", "Pokémon similar to Blaziken", "lookup", [T("similar_to", name="Blaziken")],
             fast_path=True),
    EvalCase("l2", "Where can I catch Pikachu?", "lookup", [T("encounters", pokemon="Pikachu")],
             fast_path=True),
    EvalCase("l3", "What does Intimidate do?", "lookup",
             [T("ability_info", name="Intimidate")], fast_path=True),
    EvalCase("l4", "What does Leftovers do?", "lookup", [T("item_info", name="Leftovers")],
             fast_path=True),

    # ---------------- multi-part ----------------
    EvalCase("u1", "Which Fire types learn Will-O-Wisp, and what is Fire weak to?", "multi",
             [T("learnset", move="Will-O-Wisp", types=["fire"]),
              T("type_matchup", types=["fire"])], multi_part=True),
    EvalCase("u2", "What does Earthquake do and can Garchomp learn it?", "multi",
             [T("move_info", name="Earthquake"),
              T("learnset", pokemon="Garchomp", move="Earthquake")], multi_part=True),
    EvalCase("u3", "Tell me about Snorlax and Pokémon similar to it", "multi",
             [T("similar_to", name="Snorlax")], multi_part=True),
    EvalCase("u4", "Compare Gengar and Alakazam", "multi",
             [T("get_pokemon", name="Gengar"), T("get_pokemon", name="Alakazam")],
             multi_part=True),
    EvalCase("u5", "What are Water's weaknesses and which Water types have the highest Speed?",
             "multi", [T("type_matchup", types=["water"]),
                       T("query_pokemon", types_all=["water"], sort_by="speed")],
             multi_part=True),
    EvalCase("u6", "Where can I find Eevee and what moves does it learn?", "multi",
             [T("encounters", pokemon="Eevee"), T("learnset", pokemon="Eevee")],
             multi_part=True),
    EvalCase("u7", "What do Protect and Substitute do?", "multi",
             [T("move_info", name="Protect"), T("move_info", name="Substitute")],
             multi_part=True),
    EvalCase("u8", "Which Pokémon have the highest Attack and the highest Speed?", "multi",
             [T("query_pokemon", sort_by="attack"), T("query_pokemon", sort_by="speed")],
             multi_part=True),
    EvalCase("u9", "Can Pikachu learn Surf, and who else learns Surf?", "multi",
             [T("learnset", pokemon="Pikachu", move="Surf"), T("learnset", move="Surf")],
             multi_part=True),
    EvalCase("u10", "What is Ghost weak to, and which Pokémon resemble Gengar?", "multi",
             [T("type_matchup", types=["ghost"]), T("similar_to", name="Gengar")],
             multi_part=True),
    EvalCase("u11", "What do Intimidate and Leftovers do?", "multi",
             [T("ability_info", name="Intimidate"), T("item_info", name="Leftovers")],
             multi_part=True),
    EvalCase("u12", "What is the fastest Fire type, and what is the heaviest Pokémon?", "multi",
             [T("query_pokemon", types_all=["fire"], sort_by="speed"),
              T("query_pokemon", sort_by="weight_kg")], multi_part=True),
    EvalCase("u13", "Which Ghost types learn Will-O-Wisp, and what does the move do?", "multi",
             [T("learnset", move="Will-O-Wisp", types=["ghost"]),
              T("move_info", name="Will-O-Wisp")], multi_part=True),
    EvalCase("u14", "Recommend me a Pokémon and tell me about Dragonite", "multi",
             [T("user_profile"), T("get_pokemon", name="Dragonite")], multi_part=True),
    EvalCase("u15", "Which special attackers cover Water, and what is Grass weak to?", "multi",
             [T("coverage_vs_types", targets=["water"], attacker_class="special"),
              T("type_matchup", types=["grass"])], multi_part=True),

    # ---------------- refusal / abstention ----------------
    EvalCase("r1", "What is the capital of France?", "refusal", abstain=True),
    EvalCase("r2", "Who won the 2022 World Cup?", "refusal", abstain=True),
    EvalCase("r3", "What is Bulbasaur's stock price?", "refusal", abstain=True),
]


@dataclass
class CoachCase:
    """A team-coaching question graded on the team-scope plan (and, with a key, the answer).

    ``expect_tools`` lists only *extra* steps: the team context step is always there, so a
    plain team question expects none.
    """

    id: str
    question: str
    with_opponent: bool = False
    abstain: bool = False  # LLM grading only
    expect_tools: list[ToolExpect] = field(default_factory=list)
    fast_path: bool | None = None


# A fixed Fire-heavy player team + a Rock/Water opponent that punishes it.
COACH_PLAYER_TEAM: list[int] = [6, 59, 38]  # Charizard, Arcanine, Ninetales
COACH_OPPONENT_TEAM: list[int] = [9, 76]  # Blastoise, Golem

COACH_CASES: list[CoachCase] = [
    CoachCase("c1", "What is my team's biggest defensive weakness?", fast_path=True),
    CoachCase("c2", "Best ability and EV spread for my strongest attacker?"),
    CoachCase("c3", "How should I change my team to beat this opponent?", with_opponent=True),
    CoachCase("c4", "What is Charizard's current competitive ban list status?", abstain=True),
    CoachCase("c5", "add Garchomp", expect_tools=[T("add_member", pokemon="Garchomp")],
              fast_path=True),
    CoachCase("c6", "Should I add Garchomp?", expect_tools=[T("add_member", pokemon="Garchomp")],
              fast_path=True),
    CoachCase("c7", "Give Charizard a faster set",
              expect_tools=[T("propose_set_edit", member="Charizard", side="ours")],
              fast_path=True),
    CoachCase("c8", "Draft the rest of my team — non-legendary sweepers",
              expect_tools=[T("recommend_additions", role="sweeper", legendary=False)],
              fast_path=False),
    CoachCase("c9", "Can Arcanine learn Flare Blitz?",
              expect_tools=[T("learnset", pokemon="Arcanine", move="Flare Blitz")],
              fast_path=True),
    CoachCase("c10", "Charizard vs Blastoise — who wins?", with_opponent=True,
              expect_tools=[T("duel", ours="Charizard", theirs="Blastoise")], fast_path=False),
]
