// Recorded keyless Ask answers decode, view by view, into the generated per-kind classes
// with their snake_case fields intact (the sealed union drops them; see views.dart).
import 'package:flutter_test/flutter_test.dart';
import 'package:pokerag/api/export.dart';
import 'package:pokerag/features/ask/views.dart';

import 'support/fake_backend.dart';

List<Object?> viewsOf(String name) => [
      for (final v in (fixture(name)! as Map<String, Object?>)['views']! as List) decodeView(Map<String, dynamic>.from(v as Map)),
    ];

void main() {
  final kinds = {
    'ask_learn_check': LearnCheckView,
    'ask_type_chart': TypeChartView,
    'ask_ranking': RankingView,
    'ask_multi': LearnersView,
    'ask_learnset': LearnsetView,
    'ask_move': MoveListView,
    'ask_about': PokemonListView,
  };
  for (final MapEntry(key: name, value: type) in kinds.entries) {
    test('$name decodes', () {
      final r = AskResponse.fromJson(fixture(name)! as Map<String, Object?>);
      expect(r.sources, isNotEmpty);
      final views = viewsOf(name);
      expect(views, isNotEmpty);
      expect(views.first.runtimeType, type);
    });
  }

  test('a learn check carries its verdict, step and refs', () {
    final v = viewsOf('ask_learn_check').first! as LearnCheckView;
    expect(v.ok, isTrue);
    expect(v.step, 's1');
    expect(v.chunkRefs, isNotEmpty);
  });

  test('a type chart keeps its multi-word buckets', () {
    final v = viewsOf('ask_type_chart').first! as TypeChartView;
    expect(v.weak2x, isNotEmpty);
    expect(v.chunkRefs, isNotEmpty);
  });

  test('an unknown kind decodes to null', () {
    expect(decodeView({'kind': 'not_a_view'}), isNull);
  });
}
