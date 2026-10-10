// The advanced finder: filtering and sorting over recorded catalogs (every move,
// ability and item, and the move games).
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pokerag/api/export.dart';
import 'package:pokerag/features/tools/finder_logic.dart';

import 'support/app_harness.dart';
import 'support/fake_backend.dart';

List<T> _list<T>(String name, T Function(Map<String, dynamic>) from) =>
    [for (final m in fixture(name)! as List) from(Map<String, dynamic>.from(m as Map))];

FakeBackend finderBackend() => FakeBackend((o) => switch (o.path) {
      '/api/moves' => fixture('all_moves'),
      '/api/abilities' => fixture('all_abilities'),
      '/api/items' => fixture('all_items'),
      '/api/moves/games' => fixture('move_games'),
      '/api/types' => [
          for (final (i, t) in ['normal', 'fire', 'water', 'electric', 'grass'].indexed) {'id': i + 1, 'identifier': t, 'name': t},
        ],
      '/api/pokemon' => listPage(o),
      '/api/natures' => <Object>[],
      _ => 404,
    });

Future<void> _tap(WidgetTester tester, Finder f) async {
  await tester.ensureVisible(f);
  await tester.pumpAndSettle();
  await tester.tap(f);
  await tester.pumpAndSettle();
}

String _count(WidgetTester tester) => tester.widget<Text>(find.byKey(const Key('finder-count'))).data!;

void main() {
  final moves = foldMoves(_list('all_moves', MoveOut.fromJson));

  test('same-named Z-Move copies fold into one row with both categories', () {
    final blitz = moves.where((f) => f.move.name == 'Breakneck Blitz').toList();
    expect(blitz, hasLength(1));
    expect(blitz.single.classes, containsAll(['physical', 'special']));
    // …and the folded row matches either category.
    expect(filterMoves(moves, query: 'breakneck', categories: {'special'}), hasLength(1));
  });

  test('Fire special by power: strongest first, ties by name, no status moves', () {
    final rows = filterMoves(moves, types: {'fire'}, categories: {'special'}, sort: MoveSort.power);
    expect(rows.take(3).map((f) => f.move.name), ['Blast Burn', 'Eruption', 'Mind Blown']);
    expect(rows.every((f) => f.classes.contains('special')), isTrue);
  });

  test('moves without the sorted value sink, whichever the direction', () {
    for (final asc in [true, false]) {
      final rows = filterMoves(moves, sort: MoveSort.power, ascending: asc);
      final firstNull = rows.indexWhere((f) => f.move.power == null);
      expect(rows.skip(firstNull).every((f) => f.move.power == null), isTrue, reason: 'asc=$asc');
    }
  });

  test('effects match at a word start: rain finds Drizzle, not terrain', () {
    final names = filterAbilities(_list('all_abilities', AbilityOut.fromJson), query: 'rain').map((a) => a.name);
    expect(names, containsAll(['Drizzle', 'Swift Swim']));
    expect(names.where((n) => n.contains('Surge')), isEmpty); // terrain setters
  });

  test('item categories are most-populated first', () {
    final cats = itemCategories(_list('all_items', ItemOut.fromJson));
    for (var i = 1; i < cats.length; i++) {
      expect(cats[i - 1].$2 >= cats[i].$2, isTrue);
    }
  });

  testWidgets('Lookup opens on every move; the search carries across tabs', (tester) async {
    final router = await pumpApp(tester, finderBackend(), location: '/tools');
    await _tap(tester, find.byKey(const Key('tool-lookup')));
    expect(router.state.uri.path, '/tools/lookup');
    expect(_count(tester), contains('of 901 moves'));
    await tester.enterText(find.byKey(const Key('finder-search')), 'rain');
    await tester.pumpAndSettle();
    await _tap(tester, find.byKey(const Key('finder-abilities')));
    expect(tester.widget<TextField>(find.byKey(const Key('finder-search'))).controller!.text, 'rain');
    expect(find.text('Drizzle'), findsOneWidget);
    await _tap(tester, find.byKey(const Key('finder-clear')));
    expect(_count(tester), startsWith('${_list('all_abilities', AbilityOut.fromJson).length} of'));
  });

  testWidgets('kind Max Move in Sword/Shield lists the Max Moves', (tester) async {
    await pumpApp(tester, finderBackend(), location: '/tools/lookup');
    await _tap(tester, find.byKey(const Key('filter-kind')));
    await _tap(tester, find.byKey(const Key('pick-Max Move')));
    await tester.tapAt(const Offset(195, 60)); // close the sheet
    await tester.pumpAndSettle();
    final maxCount = moves.where((f) => f.move.kind == MoveOutKind.max).length;
    expect(_count(tester), startsWith('$maxCount of'));
    await _tap(tester, find.byKey(const Key('filter-game')));
    await tester.scrollUntilVisible(find.byKey(const Key('pick-Sword / Shield')), 200, scrollable: find.byType(Scrollable).last);
    await _tap(tester, find.byKey(const Key('pick-Sword / Shield')));
    expect(_count(tester), startsWith('$maxCount of'), reason: 'the server places Max Moves in Sword/Shield');
    expect(find.text('Max Airstream'), findsOneWidget);
  });

  testWidgets('items by Fling power: highest first; a row opens its details', (tester) async {
    await pumpApp(tester, finderBackend(), location: '/tools/lookup');
    await _tap(tester, find.byKey(const Key('finder-items')));
    await _tap(tester, find.byKey(const Key('item-sort-Fling')));
    final first = find.descendant(of: find.byType(ListView).last, matching: find.byType(InkWell)).first;
    expect(find.descendant(of: first, matching: find.text('Big Nugget')), findsOneWidget);
    await _tap(tester, first);
    expect(find.byKey(const Key('item-facts')), findsOneWidget);
  });
}
