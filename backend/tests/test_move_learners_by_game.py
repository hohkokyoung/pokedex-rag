"""Per-game move learners: who learns a move in one game, and how."""

from __future__ import annotations

from sqlalchemy import select

from app.models import Move, VersionGroup
from app.services.builder import move_learners, move_learners_by_game, signature_z


async def _vg(session, identifier: str) -> int:
    stmt = select(VersionGroup.id).where(VersionGroup.identifier == identifier)
    return (await session.execute(stmt)).scalar_one()


async def _ids(session) -> tuple[int, int, int]:
    move = (await session.execute(select(Move.id).where(Move.name == "Explosion"))).scalar_one()
    return move, await _vg(session, "scarlet-violet"), await _vg(session, "ultra-sun-ultra-moon")


def _by_name(out):
    return {r.name: r for r in out.learners}


async def test_one_game_with_levels(session) -> None:
    move, sv, _ = await _ids(session)
    out = await move_learners_by_game(session, move, sv)
    assert out.version_group_id == sv == out.games[0].id
    geodude = _by_name(out)["Geodude"]
    assert [(m.method, m.level) for m in geodude.methods] == [("level-up", 36)]
    # Alolan Geodude learns it identically, so it folds into the base row.
    assert geodude.also == ["Alolan Geodude"]
    assert "Gengar" not in _by_name(out)
    # Level-up learners come first, lowest level first.
    levels = [
        next(m.level for m in r.methods if m.method == "level-up")
        for r in out.learners
        if any(m.method == "level-up" for m in r.methods)
    ]
    assert levels == sorted(levels)


async def test_defaults_to_any_game_without_duplicates(session) -> None:
    move, _, _ = await _ids(session)
    out = await move_learners_by_game(session, move)
    assert out.version_group_id is None and out.machine is None and out.last_machine is None
    names = [r.name for r in out.learners]
    assert len(names) == len(set(names))
    rows = _by_name(out)
    geodude = {m.method: m for m in rows["Geodude"].methods}
    # Level varies by game: lowest and highest are both kept.
    assert geodude["level-up"].level < geodude["level-up"].level_max
    assert "machine" in geodude
    assert "machine" in {m.method for m in rows["Gengar"].methods}
    assert out.total >= len({r.dex_number for r in out.learners})


async def test_machine_label_and_last_machine(session) -> None:
    move, sv, usum = await _ids(session)
    here = await move_learners_by_game(session, move, sv)
    assert here.machine is None
    assert (here.last_machine, here.last_machine_game) == ("TM64", "Ultra Sun / Ultra Moon")

    there = await move_learners_by_game(session, move, usum)
    assert there.machine == "TM64" and there.last_machine is None
    gengar = _by_name(there)["Gengar"]
    assert any(m.method == "machine" for m in gengar.methods)


async def test_different_form_gets_its_own_row(session) -> None:
    move, sv, _ = await _ids(session)
    rows = _by_name(await move_learners_by_game(session, move, sv))
    # Hisuian Electrode learns it at a different level than Electrode.
    assert rows["Hisuian Electrode"].form_id is not None
    assert rows["Hisuian Electrode"].methods[0].level != rows["Electrode"].methods[0].level


async def test_unknown_game_falls_back_to_any_game(session) -> None:
    move, _, _ = await _ids(session)
    assert (await move_learners_by_game(session, move, 9999)).version_group_id is None


async def test_all_time_learners_include_form_only_moves(session) -> None:
    # Only Black Kyurem (an alternate form) learns Freeze Shock.
    move = (await session.execute(select(Move.id).where(Move.name == "Freeze Shock"))).scalar_one()
    out = await move_learners(session, move)
    assert [(o.name, o.form_id is not None) for o in out] == [("Black Kyurem", True)]


async def test_signature_z_move_users(session) -> None:
    z = await signature_z(session, "catastropika")
    assert z and (z.crystal, z.base_move) == ("Pikanium Z", "Volt Tackle")
    assert [u.name for u in z.users] == ["Pikachu"]
    ultra = await signature_z(session, "light-that-burns-the-sky")
    assert ultra and ultra.users[0].form_id is not None  # Ultra Necrozma is a form
    assert await signature_z(session, "explosion") is None


async def test_move_games_lists_learnable_moves_per_game(session) -> None:
    from app.services.builder import move_games

    games = await move_games(session)
    by_id = {g.identifier: g for g in games}
    explosion, sv, _ = await _ids(session)
    assert explosion in by_id["scarlet-violet"].move_ids
    assert games[0].id == sv  # newest first
    # Flying Press debuted in Gen VI, so Gen I games can't have it.
    fp = (await session.execute(select(Move.id).where(Move.name == "Flying Press"))).scalar_one()
    assert fp not in by_id["red-blue"].move_ids and fp in by_id["x-y"].move_ids
