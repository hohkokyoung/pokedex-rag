"""Detail API embeds per-form evolution/flavor; a display-only form-moves route
serves the form learnset without touching the team-builder path."""

from __future__ import annotations

from app.services import builder, pokemon_query


async def test_galarian_darumaka_form_has_ice_stone_chain(session) -> None:
    detail = await pokemon_query.get_pokemon(session, "554")  # Darumaka species
    galar = next((f for f in detail.forms if f.id == 10176), None)
    assert galar is not None
    ids = {m.id for m in galar.evolution_members}
    assert {10176, 10177} <= ids, "expected Galarian Darumaka + Darmanitan as members"
    stage = next((s for s in galar.evolution_stages if s.to_id == 10177), None)
    assert stage is not None and "Ice Stone" in (stage.item or "")
    assert galar.flavor_texts == []  # panel will hide


async def test_form_evolution_members_carry_link_target(session) -> None:
    """Each form member must expose its base-species dex_number + form_id so the
    UI can link to /pokedex/{dex}?form={form_id} (a form id is not a dex number)."""
    detail = await pokemon_query.get_pokemon(session, "554")  # Darumaka species
    galar = next((f for f in detail.forms if f.id == 10176), None)
    assert galar is not None
    by_id = {m.id: m for m in galar.evolution_members}
    # Galarian Darumaka (form 10176) -> base species Darumaka #554
    assert by_id[10176].form_id == 10176
    assert by_id[10176].dex_number == 554
    # Galarian Darmanitan (form 10177) -> base species Darmanitan #555
    assert by_id[10177].form_id == 10177
    assert by_id[10177].dex_number == 555


async def test_species_evolution_members_link_by_dex(session) -> None:
    """Species chain members link by dex_number with no form_id."""
    detail = await pokemon_query.get_pokemon(session, "74")  # Geodude
    members = {m.name.lower(): m for m in detail.evolution_members}
    geodude = members["geodude"]
    assert geodude.form_id is None
    assert geodude.dex_number == 74


async def test_form_moves_endpoint_serves_form_learnset(session) -> None:
    rows = await builder.legal_moves_for_form(session, 10229, None)  # Hisuian Growlithe
    assert rows, "expected a Hisuian Growlithe learnset"
    assert all(r.move_id for r in rows)


async def test_species_legal_moves_unchanged(session) -> None:
    rows = await builder.legal_moves(session, 58, None)  # base Growlithe
    assert rows  # regression guard: builder path still works


async def test_regional_form_evolving_from_plain_species(session) -> None:
    """Galarian Weezing evolves from ordinary Koffing: the line is Koffing ->
    Galarian Weezing, not the base Koffing -> Weezing chain."""
    detail = await pokemon_query.get_pokemon(session, "110")  # Weezing species
    galar = next(f for f in detail.forms if f.id == 10167)
    by_id = {m.id: m for m in galar.evolution_members}
    assert set(by_id) == {109, 10167}
    assert by_id[109].form_id is None and by_id[109].dex_number == 109
    stage = next(s for s in galar.evolution_stages if s.to_id == 10167)
    assert stage.from_id == 109 and stage.min_level == 35


async def test_hisuian_line_through_plain_species(session) -> None:
    """Goomy -> Hisuian Sliggoo -> Hisuian Goodra (base stage is a plain species)."""
    detail = await pokemon_query.get_pokemon(session, "706")  # Goodra species
    hisui = next(f for f in detail.forms if f.id == 10242)
    assert {m.id for m in hisui.evolution_members} == {704, 10241, 10242}
    edges = {(s.from_id, s.to_id) for s in hisui.evolution_stages}
    assert edges == {(704, 10241), (10241, 10242)}


async def test_form_evolving_into_new_species(session) -> None:
    """Hisuian Qwilfish -> Overqwil (a form evolving into a new species)."""
    detail = await pokemon_query.get_pokemon(session, "211")  # Qwilfish species
    hisui = next(f for f in detail.forms if f.id == 10234)
    by_id = {m.id: m for m in hisui.evolution_members}
    assert set(by_id) == {10234, 904}
    assert by_id[904].form_id is None and by_id[904].dex_number == 904


async def test_alcremie_member_lists_cosmetic_variants(session) -> None:
    """Milcery -> Alcremie: the Alcremie member carries its 63 cream × sweet variants."""
    detail = await pokemon_query.get_pokemon(session, "868")  # Milcery
    alcremie = next(m for m in detail.evolution_members if m.dex_number == 869)
    assert len(alcremie.variants) == 63
    ruby = next(v for v in alcremie.variants if v.name == "Ruby Cream Strawberry Sweet")
    assert ruby.sprite_url == "/sprites/variants/869-ruby-cream-strawberry-sweet.png"
    milcery = next(m for m in detail.evolution_members if m.dex_number == 868)
    assert milcery.variants == []


async def test_gender_variants_carry_distinct_artwork(session) -> None:
    """Pyroar's Male/Female looks each point at their own artwork."""
    detail = await pokemon_query.get_pokemon(session, "668")
    pyroar = next(m for m in detail.evolution_members if m.dex_number == 668)
    assert {v.name: v.sprite_url for v in pyroar.variants} == {
        "Male": "/sprites/variants/668-male.png",
        "Female": "/sprites/variants/668-female.png",
    }


async def test_female_artwork_only_for_cosmetic_gender_differences(session) -> None:
    """Pyroar's female mane is a cosmetic look on the same record; Meowstic's female
    is its own form (form switcher), and Bulbasaur has no gender difference."""
    pyroar = await pokemon_query.get_pokemon(session, "668")
    assert pyroar.female_sprite_url == "/sprites/female/668.png"
    meowstic = await pokemon_query.get_pokemon(session, "678")
    assert meowstic.female_sprite_url is None
    bulbasaur = await pokemon_query.get_pokemon(session, "1")
    assert bulbasaur.female_sprite_url is None


async def test_dex_entries_list_every_game_once_per_text(session) -> None:
    detail = await pokemon_query.get_pokemon(session, "3")  # Venusaur
    entries = detail.flavor_entries
    # Identical wording across games is one entry carrying every game.
    texts = [e.text.lower() for e in entries]
    assert len(texts) == len(set(texts))
    games = [v for e in entries for v in e.versions]
    assert {"Red", "Blue", "Black", "White", "Sword", "Shield"} <= set(games)
    bw = next(e for e in entries if "Black" in e.versions)
    assert 5 in bw.generations
    # Soft-hyphen line breaks are rejoined ("con\xad\nvert" -> "convert").
    assert not any("con vert" in e.text or "it self" in e.text for e in entries)
