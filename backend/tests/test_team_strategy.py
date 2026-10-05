"""Unit tests for the team strategy profile (pure scoring, no DB)."""

from __future__ import annotations

from app.rag.team_summary import rules_summary
from app.schemas.analysis import DefensiveProfile, OffensiveProfile, RoleProfile, TeamAnalysis
from app.schemas.team import SlotAbility, SlotMove, TeamMemberOut, TeamOut
from app.services.stats import final_stats
from app.services.team_strategy import score_strategy, slug

SWEEPER = {"hp": 70, "attack": 130, "defense": 70, "sp_attack": 60, "sp_defense": 70, "speed": 110}
WALL = {"hp": 110, "attack": 50, "defense": 130, "sp_attack": 60, "sp_defense": 120, "speed": 40}


def _m(
    slot: int, name: str, base: dict[str, int], moves: list[str] = (), ability: str | None = None
) -> TeamMemberOut:
    return TeamMemberOut(
        slot=slot,
        pokemon_id=slot,
        dex_number=slot,
        name=name,
        types=["normal"],
        sprite_url="",
        base_stats=base,
        final_stats=final_stats(base),
        ability=SlotAbility(id=1, name=ability) if ability else None,
        nature=None,
        ev_spread={k: 0 for k in base},
        iv_spread={k: 31 for k in base},
        moves=[SlotMove(move_id=i, name=n, damage_class="status") for i, n in enumerate(moves)],
    )


def _axes(s):
    return {a.key: a for a in s.axes}


def test_slug_matches_pokeapi_identifiers() -> None:
    assert slug("Swords Dance") == "swords-dance"
    assert slug("Will-O-Wisp") == "will-o-wisp"
    assert slug("King's Shield") == "kings-shield"


def test_set_move_counts_full_learnable_counts_half() -> None:
    a = _axes(score_strategy([_m(1, "A", SWEEPER, ["Swords Dance"])], {}))
    b = _axes(score_strategy([_m(1, "A", SWEEPER)], {1: {"swords-dance"}}))
    assert a["setup"].score == 100 and a["setup"].contributors[0].set
    assert b["setup"].score == 35 and not b["setup"].contributors[0].set
    assert (b["setup"].now, b["setup"].potential) == (0, 100)


def test_tm_staples_only_count_when_set() -> None:
    # Everyone can learn Protect/Toxic — that alone must not make a team "stall".
    s = _axes(score_strategy([_m(1, "W", WALL)], {1: {"protect", "toxic", "rest"}}))
    assert s["stall"].score == 0
    assert s["support"].score == 0


def test_stall_needs_bulk_and_recovery() -> None:
    wall = _axes(score_strategy([_m(1, "W", WALL, ["Recover", "Toxic"])], {}))
    frail = _axes(score_strategy([_m(1, "S", SWEEPER, ["Recover", "Toxic"])], {}))
    assert wall["stall"].score == 100
    assert frail["stall"].score < wall["stall"].score


def test_ability_counts_as_setup_or_recovery() -> None:
    s = _axes(
        score_strategy(
            [_m(1, "B", SWEEPER, ability="Speed Boost"), _m(2, "W", WALL, ability="Regenerator")],
            {},
        )
    )
    assert s["setup"].score == 50  # one of two members
    assert s["stall"].score > 0


def test_styles() -> None:
    stall = score_strategy([_m(i, f"W{i}", WALL, ["Recover", "Toxic"]) for i in range(1, 4)], {})
    sweep = score_strategy([_m(i, f"S{i}", SWEEPER, ["Dragon Dance"]) for i in range(1, 4)], {})
    assert stall.style == "Stall"
    assert sweep.style == "Setup offense"


def test_rules_summary_is_grounded() -> None:
    members = [_m(1, "S", SWEEPER, ["Swords Dance"])]
    team = TeamOut(id=1, name="t", kind="player", members=members)
    analysis = TeamAnalysis(
        team_id=1,
        name="t",
        size=1,
        defensive=DefensiveProfile(matrix=[], shared_weaknesses=[]),
        offensive=OffensiveProfile(
            coverage_types=[],
            used_move_coverage=False,
            uncovered_types=[],
            not_super_effective=[],
            from_learnset=[],
            tips=[],
        ),
        roles=RoleProfile(members=[], missing_roles=["defensive wall"], notes=[]),
        suggestions=[],
        vs_opponent=None,
        summary=[],
    )
    text = rules_summary(team, score_strategy(members, {}), analysis)
    # Describes the team only — no risks or advice.
    assert text.startswith("A setup offense Normal team")
    assert "Swords Dance" in text
    assert "wall" not in text and "risk" not in text


def test_fingerprint_ignores_name_and_move_order() -> None:
    from app.rag.team_summary import fingerprint

    a = _m(1, "S", SWEEPER, ["Swords Dance", "Earthquake"])
    b = _m(1, "S", SWEEPER, ["Earthquake", "Swords Dance"])
    # Same moves in a different order: give them matching ids so only order differs.
    b.moves = list(reversed(a.moves))
    t1 = TeamOut(id=1, name="Alpha", kind="player", members=[a])
    t2 = TeamOut(id=1, name="Renamed", kind="player", members=[b])
    assert fingerprint(t1) == fingerprint(t2)


def test_fingerprint_changes_with_roster() -> None:
    from app.rag.team_summary import fingerprint

    t1 = TeamOut(id=1, name="t", kind="player", members=[_m(1, "S", SWEEPER, ["Swords Dance"])])
    t2 = TeamOut(
        id=1, name="t", kind="player", members=[_m(1, "S", SWEEPER, ["Swords Dance", "Roost"])]
    )
    t3 = TeamOut(
        id=1,
        name="t",
        kind="player",
        members=[_m(1, "S", SWEEPER, ["Swords Dance"], ability="Moxie")],
    )
    assert len({fingerprint(t1), fingerprint(t2), fingerprint(t3)}) == 3
