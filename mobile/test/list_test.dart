import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'support/app_harness.dart';
import 'support/fake_backend.dart';

FakeBackend backend({int total = 95}) => FakeBackend((o) => switch (o.path) {
      '/api/pokemon' => listPage(o, total: total),
      '/api/types/chart' => fixture('type_chart'),
      '/api/generations' => [
          for (var i = 1; i <= 9; i++) {'id': i, 'identifier': 'generation-$i', 'name': 'Generation $i'},
        ],
      _ => 404,
    });

void main() {
  testWidgets('the first page shows Bulbasaur with its types', (tester) async {
    await pumpApp(tester, backend());
    expect(find.text('Bulbasaur'), findsOneWidget);
    expect(find.text('#001'), findsOneWidget);
    expect(find.text('Grass'), findsWidgets);
    expect(find.text('Poison'), findsWidgets);
  });

  testWidgets('scrolling near the end appends the next page; nothing loads past the end', (tester) async {
    final be = backend(total: 95);
    await pumpApp(tester, be);
    expect(be.hits['/api/pokemon'], 1);
    for (var i = 0; i < 30 && find.text('Mon95').evaluate().isEmpty; i++) {
      await tester.drag(find.byType(ListView), const Offset(0, -2500));
      await tester.pumpAndSettle();
    }
    expect(find.text('Mon95'), findsOneWidget);
    expect(be.hits['/api/pokemon'], 3); // 40 + 40 + 15, then no fourth request
    await tester.drag(find.byType(ListView), const Offset(0, -2500));
    await tester.pumpAndSettle();
    expect(be.hits['/api/pokemon'], 3);
    final offsets = be.requests.where((r) => r.path == '/api/pokemon').map((r) => r.queryParameters['offset']);
    expect(offsets, [0, 40, 80]);
  });

  testWidgets('no matches says so and offers to clear the search', (tester) async {
    await pumpApp(tester, backend(total: 0));
    await tester.enterText(find.byKey(const Key('search')), 'zzz');
    await tester.pump(const Duration(milliseconds: 300));
    await tester.pumpAndSettle();
    expect(find.text('No Pokémon match.'), findsOneWidget);
    expect(find.byKey(const Key('clear-filters')), findsOneWidget);
  });

  testWidgets('search, type, generation and sort each reload from page 1', (tester) async {
    final be = backend(total: 95);
    // Tall enough that the whole filter sheet fits with the test font (its glyphs are
    // wider than the real ones; on a real phone the sheet fits as is).
    await pumpApp(tester, be, size: const Size(390, 1400));
    Map<String, dynamic> last() => be.requests.lastWhere((r) => r.path == '/api/pokemon').queryParameters;
    var seen = 0;
    // The first list request since the last check (a reload must start at offset 0).
    Map<String, dynamic> next() {
      final list = be.requests.where((r) => r.path == '/api/pokemon').toList();
      final r = list[seen];
      seen = list.length;
      return r.queryParameters;
    }

    for (var i = 0; i < 10 && (be.hits['/api/pokemon'] ?? 0) < 2; i++) {
      await tester.drag(find.byType(ListView), const Offset(0, -2500));
      await tester.pumpAndSettle();
    }
    expect(last()['offset'], greaterThan(0));
    next();

    await tester.enterText(find.byKey(const Key('search')), 'garch');
    await tester.pump(const Duration(milliseconds: 300));
    await tester.pumpAndSettle();
    final afterSearch = next();
    expect(afterSearch['offset'], 0);
    expect(afterSearch['q'], 'garch');

    await tester.tap(find.byKey(const Key('filters')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('type-dragon')));
    await tester.pumpAndSettle();
    final afterType = next();
    expect(afterType['type'], ['dragon']);
    expect(afterType['offset'], 0);

    await tester.tap(find.byKey(const Key('gen-4')));
    await tester.pumpAndSettle();
    expect(next()['generation'], [4]);

    await tester.tap(find.byKey(const Key('sort-speed')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('order')));
    await tester.pumpAndSettle();
    expect(last()['sort'], 'speed');
    expect(last()['order'], 'desc');
    expect(last()['q'], 'garch'); // filters keep the search
    // Rows lead with the stat being sorted by.
    await tester.tapAt(const Offset(195, 20)); // close the sheet
    await tester.pumpAndSettle();
    expect(find.text('SPE'), findsWidgets);
    expect(find.text('BST'), findsNothing);
  });

  testWidgets('a third type replaces the oldest (two at most)', (tester) async {
    final be = backend();
    await pumpApp(tester, be);
    await tester.tap(find.byKey(const Key('filters')));
    await tester.pumpAndSettle();
    for (final t in ['fire', 'water', 'grass']) {
      await tester.tap(find.byKey(Key('type-$t')));
      await tester.pumpAndSettle();
    }
    expect(be.requests.lastWhere((r) => r.path == '/api/pokemon').queryParameters['type'], ['water', 'grass']);
  });
}
