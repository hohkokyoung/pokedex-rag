import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pokerag/api/export.dart';
import 'package:pokerag/data/server.dart';

import 'support/app_harness.dart';
import 'support/fake_backend.dart';

FakeBackend detailBackend({Completer<void>? chartGate}) => FakeBackend((o) => switch (o.path) {
      '/api/pokemon/445' => fixture('garchomp'),
      '/api/pokemon/133' => fixture('eevee'),
      '/api/pokemon/869' => fixture('alcremie'),
      '/api/types/chart' => fixture('type_chart'),
      '/api/pokemon/445/moves/by-game' => fixture(o.queryParameters['version_group'] == 20 ? 'garchomp_moves_swsh' : 'garchomp_moves_sv'),
      '/api/moves/89/learners/by-game' => fixture('earthquake_learners_sv'),
      '/api/pokemon/445/encounters' => fixture('garchomp_encounters'),
      '/api/profile' => fixture('profile'),
      '/api/pokemon' => listPage(o, total: 1025),
      _ when o.path.endsWith('/moves/by-game') => {'version_group_id': null, 'games': <Object>[], 'moves': <Object>[]},
      _ when o.path.endsWith('/encounters') => {'version_id': null, 'games': <Object>[], 'encounters': <Object>[]},
      _ => 404,
    });

List<String> chipsIn(WidgetTester tester, Finder row) => tester
    .widgetList<Text>(find.descendant(of: row, matching: find.byType(Text)))
    .map((t) => t.data ?? '')
    .toList();

void main() {
  testWidgets('Garchomp: types, total, hidden ability, ×4 and Hits ×2', (tester) async {
    await pumpApp(tester, detailBackend(), location: '/pokemon/445');
    expect(find.text('Garchomp'), findsWidgets);
    expect(find.text('Total 600'), findsOneWidget);
    await tester.scrollUntilVisible(find.text('Rough Skin'), 200);
    expect(find.text('Rough Skin'), findsOneWidget);
    expect(find.text('Hidden'), findsOneWidget);
    await tester.scrollUntilVisible(find.byKey(const Key('hits-row')), 200);
    final hits = chipsIn(tester, find.byKey(const Key('hits-row')));
    expect(hits, containsAllInOrder(['Hits', '×2', 'Fire', 'Electric', 'Poison', 'Rock', 'Dragon', 'Steel']));
    expect(chipsIn(tester, find.ancestor(of: find.text('×4'), matching: find.byType(Row)).first), contains('Ice'));
    await tester.pumpAndSettle(); // let sections that scrolled into view finish loading
  });

  testWidgets('switching to Mega Garchomp swaps stats, abilities and artwork', (tester) async {
    await pumpApp(tester, detailBackend(), location: '/pokemon/445');
    final mega = PokemonDetail.fromJson(fixture('garchomp')! as Map<String, Object?>).forms.firstWhere((f) => f.name == 'Mega Garchomp');
    await tester.tap(find.byKey(Key('form-${mega.id}')));
    await tester.pumpAndSettle();
    expect(find.text('Mega Garchomp'), findsWidgets);
    expect(find.text('Total ${mega.stats.total}'), findsOneWidget);
    expect(find.byKey(ValueKey('art:$defaultAddress${mega.spriteUrl}')), findsOneWidget);
    await tester.scrollUntilVisible(find.text(mega.abilities.first.name), 200);
    expect(find.text('Rough Skin'), findsNothing);
    await tester.pump(const Duration(seconds: 2));
  });

  testWidgets('the type chart is requested once across several Pokémon', (tester) async {
    final be = detailBackend();
    final router = await pumpApp(tester, be, location: '/pokemon/445');
    for (final id in ['133', '869', '445']) {
      router.push('/pokemon/$id');
      await tester.pumpAndSettle();
      await tester.scrollUntilVisible(find.byKey(const Key('hits-row')), 300, scrollable: find.byType(Scrollable).last);
    }
    expect(be.hits['/api/types/chart'], 1);
  });

  testWidgets('evolution chips render exactly as the server labels them', (tester) async {
    await pumpApp(tester, detailBackend(), location: '/pokemon/133');
    await tester.scrollUntilVisible(find.text('Evolution'), 300);
    await tester.pumpAndSettle();
    expect(find.text('Water Stone'), findsOneWidget);
    expect(find.text('Friendship'), findsNWidgets(2)); // Espeon (Day) and Umbreon (Night)
    expect(find.text('Day'), findsOneWidget);
    expect(find.text('Affection'), findsOneWidget);
    // The description is a tap away, verbatim.
    final espeon = PokemonDetail.fromJson(fixture('eevee')! as Map<String, Object?>)
        .evolutionStages
        .firstWhere((s) => s.toName == 'Espeon');
    final dayRow = find.ancestor(of: find.text('Day'), matching: find.byType(Wrap)).first;
    await tester.tap(find.descendant(of: dayRow, matching: find.byKey(const Key('evo-explain'))));
    await tester.pumpAndSettle();
    expect(find.text(espeon.display!.description!), findsOneWidget);
  });

  testWidgets('Alcremie shows the spin guide', (tester) async {
    await pumpApp(tester, detailBackend(), location: '/pokemon/869');
    await tester.scrollUntilVisible(find.text('Cream · how to spin (9)'), 400);
    expect(find.text('Sweet · the topping (7)'), findsOneWidget);
    expect(find.text('Give Milcery a Sweet to hold.'), findsOneWidget);
    await tester.scrollUntilVisible(find.text('Rainbow Swirl'), 200);
    expect(find.text('Vanilla Cream'), findsOneWidget);
  });

  testWidgets('with reduced motion the stat bars are already full', (tester) async {
    await pumpApp(tester, detailBackend(), location: '/pokemon/445');
    // Normal motion: right after a rebuild the bars start empty and draw in.
    final animated = tester.widgetList<FractionallySizedBox>(find.byKey(const Key('stat-fill')));
    expect(animated.every((b) => b.widthFactor! > 0), isTrue); // settled by now

    tester.platformDispatcher.accessibilityFeaturesTestValue = const FakeAccessibilityFeatures(disableAnimations: true);
    addTearDown(tester.platformDispatcher.clearAccessibilityFeaturesTestValue);
    await pumpApp(tester, detailBackend(), location: '/pokemon/445');
    await tester.pump(); // one frame, no settling
    final bars = tester.widgetList<FractionallySizedBox>(find.byKey(const Key('stat-fill'))).toList();
    expect(bars, isNotEmpty);
    // Garchomp's Attack is 130/255: at rest immediately, no draw-in.
    expect(bars.map((b) => b.widthFactor), contains(closeTo(130 / 255, 0.001)));
  });
}
