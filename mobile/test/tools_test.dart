// The Tools tab: type calculator, nature helper, catch rate and lookup, over recorded
// server responses.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pokerag/api/export.dart';
import 'package:pokerag/features/tools/type_calc_screen.dart';

import 'support/app_harness.dart';
import 'support/fake_backend.dart';

FakeBackend toolsBackend() => FakeBackend((o) {
      final p = o.path;
      final q = o.queryParameters;
      if (p == '/api/pokemon/149/catch') return fixture('${q['status']}' == 'sleep' ? 'catch_149_sleep' : 'catch_149');
      if (p == '/api/abilities/22/pokemon') return fixture('holders_intimidate');
      return switch (p) {
        '/api/types/chart' => fixture('type_chart'),
        '/api/natures' => fixture('natures'),
        '/api/moves' => q['q'] == 'leftovers' ? fixture('look_moves_leftovers') : <Object>[],
        '/api/abilities' => switch (q['q']) {
            'leftovers' => fixture('look_abilities_leftovers'),
            'intimidate' => fixture('look_abilities_intimidate'),
            _ => <Object>[],
          },
        '/api/items' => q['q'] == 'leftovers' ? fixture('look_items_leftovers') : <Object>[],
        '/api/pokemon' => listPage(o),
        _ => 404,
      };
    });

Future<void> _tap(WidgetTester tester, Finder f) async {
  await tester.ensureVisible(f);
  await tester.pumpAndSettle();
  await tester.tap(f);
  await tester.pumpAndSettle();
}

Future<void> _search(WidgetTester tester, String q) async {
  await tester.enterText(find.byKey(const Key('lookup-field')), q);
  await tester.pump(const Duration(milliseconds: 250));
  await tester.pumpAndSettle();
}

void main() {
  test('Fire/Flying: Rock ×4, Ground immune, hits Grass ×2', () {
    final chart = TypeChartOut.fromJson(Map<String, dynamic>.from(fixture('type_chart')! as Map));
    final r = typeCalc(chart, ['fire', 'flying']);
    expect(r.x4, ['rock']);
    expect(r.immune, ['ground']);
    expect(r.hits, containsAll(['grass', 'bug', 'ice', 'steel', 'fighting']));
  });

  testWidgets('the Tools tab lists the tools and opens one, keeping the tab', (tester) async {
    final router = await pumpApp(tester, toolsBackend());
    await _tap(tester, find.byKey(const Key('tab-tools')));
    for (final t in ['types', 'natures', 'catch', 'lookup']) {
      expect(find.byKey(Key('tool-$t')), findsOneWidget);
    }
    await _tap(tester, find.byKey(const Key('tool-catch')));
    expect(router.state.uri.path, '/tools/catch');
    await tester.pageBack();
    await tester.pumpAndSettle();
    expect(router.state.uri.path, '/tools');
  });

  testWidgets('type calculator: Fire + Flying, and a third pick replaces the oldest', (tester) async {
    await pumpApp(tester, toolsBackend(), location: '/tools/types');
    await _tap(tester, find.byKey(const Key('calc-flying')));
    expect(find.text('Fire / Flying'), findsOneWidget);
    expect(find.descendant(of: find.byKey(const Key('calc-row-x4')), matching: find.text('Rock')), findsOneWidget);
    expect(find.descendant(of: find.byKey(const Key('calc-row-immune')), matching: find.text('Ground')), findsOneWidget);
    await _tap(tester, find.byKey(const Key('calc-water')));
    expect(find.text('Flying / Water'), findsOneWidget);
  });

  testWidgets('nature helper: Adamant is +Atk / −SpA, Hardy is neutral', (tester) async {
    await pumpApp(tester, toolsBackend(), location: '/tools/natures');
    expect(find.textContaining('+Atk', findRichText: true), findsWidgets);
    final note = tester.widget<Text>(find.byKey(const Key('nature-note'))).textSpan!.toPlainText();
    expect(note, 'Adamant — +Atk / −SpA (±10%)');
    await _tap(tester, find.byKey(const Key('nature-Hardy')));
    expect(tester.widget<Text>(find.byKey(const Key('nature-note'))).textSpan!.toPlainText(), 'Hardy — neutral, no stat changes');
  });

  testWidgets('catch rate: the server ranks, and Sleep asks again', (tester) async {
    final be = toolsBackend();
    // Tall enough that all 20 balls are built, to compare their order on screen.
    await pumpApp(tester, be, location: '/tools/catch', size: const Size(390, 2600));
    final first = be.requests.lastWhere((r) => r.path == '/api/pokemon/149/catch');
    expect(first.queryParameters['hp_pct'], 25);
    expect(first.queryParameters['level'], 55);
    expect(find.byKey(const Key('ball-dream')), findsOneWidget);
    double y(String id) => tester.getTopLeft(find.byKey(Key('ball-$id'))).dy;
    expect(y('ultra'), lessThan(y('dream')));

    await _tap(tester, find.byKey(const Key('status-sleep')));
    expect(be.requests.lastWhere((r) => r.path == '/api/pokemon/149/catch').queryParameters['status'].toString(), 'sleep'); // an enum whose toString is the wire value
    expect(y('dream'), lessThan(y('ultra')));
    expect(find.byKey(const Key('catch-math')), findsOneWidget);
  });

  testWidgets("catch rate: a stopped server shows the can't-reach state", (tester) async {
    final be = toolsBackend()..down = true;
    await pumpApp(tester, be, location: '/tools/catch');
    expect(find.text("Can't reach the server"), findsOneWidget);
  });

  testWidgets('lookup: leftovers finds the item and opens its effect', (tester) async {
    await pumpApp(tester, toolsBackend(), location: '/tools/lookup');
    await _search(tester, 'leftovers');
    expect(find.text('Items'), findsOneWidget);
    await _tap(tester, find.text('Leftovers').first);
    expect(find.byKey(const Key('item-effect')), findsOneWidget);
    expect(find.byKey(const Key('item-facts')), findsOneWidget);
  });

  testWidgets('lookup: Intimidate holders filter to Gyarados, which opens its page', (tester) async {
    final router = await pumpApp(tester, toolsBackend(), location: '/tools/lookup');
    await _search(tester, 'intimidate');
    await _tap(tester, find.byKey(const Key('look-ability-22')));
    expect(find.byKey(const Key('ability-effect')), findsOneWidget);
    await tester.enterText(find.byKey(const Key('holders-filter')), 'gyara');
    await tester.pumpAndSettle();
    await _tap(tester, find.text('Gyarados'));
    expect(router.state.uri.path, '/pokemon/130');
  });
}
