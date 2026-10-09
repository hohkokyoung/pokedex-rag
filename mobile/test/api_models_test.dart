// The generated models decode real backend responses (recorded from the running app).
import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:pokerag/api/export.dart';

Map<String, Object?> fixture(String name) =>
    jsonDecode(File('test/fixtures/$name.json').readAsStringSync()) as Map<String, Object?>;

void main() {
  test('Garchomp detail decodes', () {
    final d = PokemonDetail.fromJson(fixture('garchomp'));
    expect(d.name, 'Garchomp');
    expect(d.types, ['dragon', 'ground']);
    expect(d.stats.total, 600);
    expect(d.abilities.firstWhere((a) => a.name == 'Rough Skin').isHidden, isTrue);
    expect(d.matchups.weak4x, ['ice']);
    expect(d.forms.map((f) => f.name), contains('Mega Garchomp'));
  });

  test('evolution labels and the spin guide decode', () {
    final eevee = PokemonDetail.fromJson(fixture('eevee'));
    final espeon = eevee.evolutionStages.firstWhere((s) => s.toName == 'Espeon');
    expect(espeon.display!.chips.map((c) => c.label), ['Friendship', 'Day']);
    expect(espeon.display!.chips.first.tone, EvolutionChipTone.solid);
    final alcremie = PokemonDetail.fromJson(fixture('alcremie'));
    expect(alcremie.spinGuide!.creams, hasLength(9));
  });

  test('a list page decodes', () {
    final page = PokemonListResponse.fromJson(fixture('list_page1'));
    expect(page.items.first.name, 'Bulbasaur');
    expect(page.items, hasLength(40));
    expect(page.total, greaterThan(1000));
  });

  test('the type chart decodes', () {
    final c = TypeChartOut.fromJson(fixture('type_chart'));
    expect(c.order, hasLength(18));
    expect(c.chart['ground']!['flying'], 0);
  });
}
