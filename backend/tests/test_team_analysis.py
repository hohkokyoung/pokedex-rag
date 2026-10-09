"""Unit tests for the deterministic team-analysis helpers (pure, no DB)."""

from __future__ import annotations

import pytest

from app.schemas.analysis import OffensiveProfile, RoleProfile
from app.schemas.team import TeamMemberOut
from app.services.battle import Attack, Fighter, best_hit, complete_moveset, damage_pct
from app.services.team_analysis import (
    _best_ability,
    _best_spread,
    _classify,
    _defensive,
    _exchange,
    _head_to_head,
    _roles,
    _summary,
)


def _member(slot: int, name: str, types: list[str], base: dict[str, int]) -> TeamMemberOut:
    return TeamMemberOut(
        slot=slot,
        pokemon_id=slot,
        dex_number=slot,
        name=name,
        types=types,
        sprite_url="",
        base_stats=base,
        final_stats=base,
        ability=None,
        nature=None,
        ev_spread={k: 0 for k in base},
        iv_spread={k: 31 for k in base},
        moves=[],
    )


FAST_ATTACKER = {
    "hp": 78, "attack": 84, "defense": 78, "sp_attack": 109, "sp_defense": 85, "speed": 100
}
WALL = {"hp": 100, "attack": 60, "defense": 130, "sp_attack": 60, "sp_defense": 130, "speed": 40}


def test_classify_roles() -> None:
    assert _classify(speed=100, offense=109, bulk=241) == "Fast attacker"
    assert _classify(speed=40, offense=60, bulk=360) == "Wall"
    assert _classify(speed=50, offense=130, bulk=200) == "Wallbreaker"


def test_shared_weakness_threshold() -> None:
    members = [
        _member(1, "A", ["fire", "flying"], FAST_ATTACKER),
        _member(2, "B", ["fire"], FAST_ATTACKER),
        _member(3, "C", ["fire"], FAST_ATTACKER),
    ]
    # All three weak to rock; only C+B+A -> shared (>=3).
    mults = {
        1: {"rock": 4.0, "water": 2.0},
        2: {"rock": 2.0, "water": 2.0},
        3: {"rock": 2.0, "water": 2.0},
    }
    prof = _defensive(members, mults)
    shared = {w.type: w.count for w in prof.shared_weaknesses}
    assert shared.get("rock") == 3
    assert shared.get("water") == 3
    # Matrix records per-member weak_to and drops neutral multipliers.
    row = next(m for m in prof.matrix if m.slot == 1)
    assert "rock" in row.weak_to
    assert row.multipliers["rock"] == 4.0


def test_roles_missing_wall_and_speed() -> None:
    slow_frail = {
        "hp": 50, "attack": 60, "defense": 50, "sp_attack": 60, "sp_defense": 50, "speed": 50
    }
    prof = _roles([_member(1, "A", ["normal"], slow_frail)])
    assert "fast attacker / speed control" in prof.missing_roles
    assert "defensive wall" in prof.missing_roles


def test_best_spread_fast_special() -> None:
    nature, evs, rationale = _best_spread("Alakazam", FAST_ATTACKER)
    assert nature == "Timid"  # special attacker with high speed
    assert evs["sp_attack"] == 252 and evs["speed"] == 252
    assert "Alakazam" in rationale


def test_best_ability_prefers_stronger_effect() -> None:
    name, _reason = _best_ability(
        [
            ("Run Away", "Enables a sure getaway from wild Pokémon."),
            ("Speed Boost", "Its Speed stat is boosted every turn."),
        ]
    )
    assert name == "Speed Boost"


def test_summary_mentions_partial_team_and_weakness() -> None:
    members = [_member(1, "A", ["fire", "flying"], FAST_ATTACKER)]
    prof = _defensive(members, {1: {"rock": 4.0}})
    summary = _summary(
        size=1,
        defensive=prof,
        offensive=OffensiveProfile(
            coverage_types=["fire"],
            used_move_coverage=False,
            uncovered_types=["rock"],
            not_super_effective=[],
        ),
        roles=RoleProfile(members=[], missing_roles=["defensive wall"], notes=[]),
        vs=None,
    )
    joined = " ".join(summary)
    assert "1/6" in joined
    assert "rock" in joined.lower()


def _fighter(
    slot: int, name: str, types: list[str], stats: dict[str, int],
    moves: list[Attack], mults: dict[str, float] | None = None,
) -> Fighter:
    f = Fighter(
        slot=slot, name=name, types=types, stats=stats, ability=None,
        def_mults=mults or {}, set_attacks=moves, open_slots=4 - len(moves),
    )
    f.moves = list(moves)
    return f


STATS = {
    "hp": 150, "attack": 120, "defense": 100, "sp_attack": 120, "sp_defense": 100, "speed": 100
}
SURF = Attack(1, "Surf", "water", "special", 90, 100)
EMBER = Attack(2, "Ember", "fire", "special", 40, 100)
TACKLE = Attack(3, "Tackle", "normal", "physical", 40, 100)
QUICK = Attack(4, "Quick Attack", "normal", "physical", 40, 100, priority=1)
THUNDER_PUNCH = Attack(5, "Thunder Punch", "electric", "physical", 75, 100, learned=True)


def test_type_and_power_edge_wins_pairing() -> None:
    ours = [_fighter(1, "Wet", ["water"], STATS, [SURF], {"fire": 0.5, "water": 0.5})]
    theirs = [_fighter(1, "Hot", ["fire"], STATS, [EMBER], {"water": 2.0, "fire": 0.5})]
    h = _head_to_head(ours, theirs)
    (cell,) = h.cells
    assert cell.our_move == "Surf" and cell.our_hit == 2.0
    assert cell.our_hko < cell.their_hko
    assert cell.outcome == "win"
    assert h.pressure[0].targets == ["Hot"]
    assert h.verdict is not None and h.verdict.edge == "ours"


def test_equal_trade_goes_to_whoever_moves_first() -> None:
    slow = {**STATS, "speed": 50}
    ours = [_fighter(1, "Quick", ["normal"], STATS, [TACKLE])]
    theirs = [_fighter(1, "Slow", ["normal"], slow, [TACKLE])]
    (cell,) = _head_to_head(ours, theirs).cells
    assert cell.our_hko == cell.their_hko
    # Neutral Tackles take many hits: a near-equal slugfest reads as close.
    assert cell.outcome == "even"
    assert _exchange(2, 2, "ours") == "win"
    assert _exchange(2, 2, "theirs") == "lose"
    assert _exchange(2, 2, "tie") == "even"


def test_priority_beats_speed() -> None:
    slow = {**STATS, "speed": 30}
    ours = [_fighter(1, "Priority", ["normal"], slow, [QUICK])]
    theirs = [_fighter(1, "Fast", ["normal"], STATS, [TACKLE])]
    assert _head_to_head(ours, theirs).cells[0].faster == "ours"


def test_learnset_fills_open_slots_with_coverage() -> None:
    # A Fire attacker with a Water target: the learnable Thunder Punch is picked.
    blaz = Fighter(
        slot=1, name="Blaziken", types=["fire", "fighting"], stats=STATS, ability=None,
        def_mults={}, set_attacks=[EMBER], open_slots=3, pool=[THUNDER_PUNCH],
    )
    gyara = _fighter(1, "Gyarados", ["water", "flying"], STATS, [], {"electric": 4.0, "fire": 0.5})
    moves = complete_moveset(blaz, [gyara])
    assert [m.name for m in moves] == ["Ember", "Thunder Punch"]
    blaz.moves = moves
    hit = best_hit(blaz, gyara)
    assert hit.attack == THUNDER_PUNCH and hit.mult == 4.0


def test_ability_immunity_zeroes_damage() -> None:
    ground = Attack(6, "Earthquake", "ground", "physical", 100, 100)
    att = _fighter(1, "Quaker", ["ground"], STATS, [ground])
    floater = _fighter(1, "Floater", ["ghost"], STATS, [], {"ground": 0.0})
    assert damage_pct(att, ground, floater) == 0
    assert best_hit(att, floater).hko == 99


def test_head_to_head_empty_side_has_no_verdict() -> None:
    ours = [_fighter(1, "A", ["normal"], STATS, [TACKLE])]
    assert _head_to_head(ours, []).verdict is None


def test_foul_play_uses_target_attack() -> None:
    foul = Attack(7, "Foul Play", "dark", "physical", 95, 100)
    weak = _fighter(1, "Weak", ["normal"], {**STATS, "attack": 20}, [foul])
    strong_t = _fighter(1, "Strong", ["normal"], {**STATS, "attack": 200}, [])
    weak_t = _fighter(2, "Feeble", ["normal"], {**STATS, "attack": 20}, [])
    assert damage_pct(weak, foul, strong_t) > damage_pct(weak, foul, weak_t)


# ── sets: items, abilities, setup ────────────────────────────────────────────
from app.services import battle, sets  # noqa: E402

BULKY = {**STATS, "hp": 200, "defense": 140, "sp_defense": 140}
CLOSE_COMBAT = Attack(6, "Close Combat", "fighting", "physical", 120, 100)


def test_setup_move_is_used_when_it_wins_the_pairing() -> None:
    sweeper = _fighter(1, "Sweeper", ["normal"], STATS, [TACKLE])
    wall = _fighter(1, "Wall", ["normal"], BULKY, [TACKLE])
    plain = battle.duel(sweeper, wall)
    sweeper.setup = sets.Setup("Swords Dance", {"attack": 2})
    boosted = battle.duel(sweeper, wall)
    assert boosted.a_setup == "Swords Dance"
    assert boosted.a_hit.pct > plain.a_hit.pct
    assert boosted.a_turns <= plain.a_turns


def test_choice_scarf_flips_who_moves_first() -> None:
    slow = {**STATS, "speed": 80}
    ours = _fighter(1, "Scarfer", ["normal"], slow, [TACKLE])
    theirs = _fighter(1, "Fast", ["normal"], STATS, [TACKLE])
    assert battle.duel(ours, theirs).first == "theirs"
    ours.item = "choice-scarf"
    assert battle.duel(ours, theirs).first == "ours"


def test_focus_sash_survives_a_one_hit_ko() -> None:
    frail = {**STATS, "hp": 60, "defense": 50}
    attacker = _fighter(1, "Hitter", ["fighting"], STATS, [CLOSE_COMBAT])
    target = _fighter(1, "Frail", ["normal"], frail, [TACKLE], {"fighting": 2.0})
    assert battle.duel(attacker, target).a_turns == 1
    target.item = "focus-sash"
    assert battle.duel(attacker, target).a_turns == 2


def test_life_orb_and_choice_band_raise_damage() -> None:
    a = _fighter(1, "A", ["normal"], STATS, [TACKLE])
    b = _fighter(1, "B", ["normal"], BULKY, [TACKLE])
    base = battle.damage_pct(a, TACKLE, b)
    a.item = "life-orb"
    assert battle.damage_pct(a, TACKLE, b) == pytest.approx(base * 1.3, rel=0.02)
    a.item = "choice-band"
    assert battle.damage_pct(a, TACKLE, b) > base * 1.3


def test_best_setup_prefers_the_attackers_stat() -> None:
    moves = [("Calm Mind", "calm-mind"), ("Swords Dance", "swords-dance")]
    assert sets.best_setup(moves, physical=True).name == "Swords Dance"  # type: ignore[union-attr]
    assert sets.best_setup(moves, physical=False).name == "Calm Mind"  # type: ignore[union-attr]
    assert sets.best_setup([("Protect", "protect")], physical=True) is None


def test_duel_log_records_setup_attacks_and_faint() -> None:
    sweeper = _fighter(1, "Sweeper", ["normal"], STATS, [TACKLE])
    sweeper.setup = sets.Setup("Swords Dance", {"attack": 2})
    wall = _fighter(1, "Wall", ["normal"], BULKY, [TACKLE])
    d = battle.duel(sweeper, wall)
    kinds = [e["kind"] for e in d.log]
    assert "attack" in kinds and "faint" in kinds
    if d.a_setup:
        assert d.log[0]["kind"] == "setup" and d.log[0]["move"] == "Swords Dance"


def test_suggested_item_follows_the_role() -> None:
    """The engine suggests a held item per member (moved from the website's TeamReport)."""
    from app.services.team_analysis import _suggest_item

    garchomp = _member(1, "Garchomp", ["dragon", "ground"], {
        "hp": 108, "attack": 130, "defense": 95, "sp_attack": 80, "sp_defense": 85, "speed": 102})
    gengar = _member(2, "Gengar", ["ghost", "poison"], {
        "hp": 60, "attack": 65, "defense": 60, "sp_attack": 130, "sp_defense": 75, "speed": 110})
    frail = _member(3, "Abra", ["psychic"], {
        "hp": 25, "attack": 20, "defense": 15, "sp_attack": 105, "sp_defense": 55, "speed": 90})
    assert _suggest_item(garchomp, "Wall") == "Leftovers"
    assert _suggest_item(garchomp, "Tank") == "Leftovers"
    assert _suggest_item(garchomp, "Wallbreaker") == "Choice Band"
    assert _suggest_item(gengar, "Wallbreaker") == "Choice Specs"
    assert _suggest_item(garchomp, "Fast attacker") == "Life Orb"
    assert _suggest_item(frail, "Attacker") == "Focus Sash"  # HP+Def+SpD < 200
    assert _suggest_item(garchomp, "Balanced") == "Leftovers"
    assert _suggest_item(garchomp, None) == "Leftovers"
