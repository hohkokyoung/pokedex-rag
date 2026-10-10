// The damage calculator: the app sets up the state, the server plays the turn
// (recorded responses from POST /api/calc/turn).

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pokerag/api/export.dart';
import 'package:pokerag/features/tools/calc_state.dart';

import 'support/app_harness.dart';
import 'support/calc_backend.dart';
import 'support/fake_backend.dart';


Future<void> _tap(WidgetTester tester, Finder f) async {
  // The calculator is a long lazy list: scroll until the target is built.
  if (f.evaluate().isEmpty) await tester.scrollUntilVisible(f, 300, scrollable: find.byType(Scrollable).first);
  await tester.ensureVisible(f);
  await tester.pumpAndSettle();
  await tester.tap(f);
  await tester.pumpAndSettle();
}

void main() {
  test('Offensive on a special attacker is Modest 252 SpA / 252 Spe / 4 HP', () {
    final s = CalcSet.offensive(
      const CalcPick(pokemonId: 94, name: 'Gengar', spriteUrl: '', types: ['ghost', 'poison'], attack: 65, spAttack: 130),
    );
    expect(s.nature, 'Modest');
    expect(s.ev, {'hp': 4, 'atk': 0, 'def': 0, 'spa': 252, 'spd': 0, 'spe': 252});
    expect(s.iv['atk'], 0);
  });

  test('EVs are capped at 252 each and 510 in total', () {
    final s = CalcSet.offensive(); // 4 HP / 252 Atk / 252 Spe = 508
    expect(s.withEv('def', 100).ev['def'], 2);
    expect(s.withEv('atk', 300).ev['atk'], 252);
    expect(s.withEv('def', 100).pre, 'Custom');
  });

  test('moves list damaging first: STAB, then power', () {
    final moves = calcMoveOrder(
      [for (final m in fixture('learnset_445')! as List) LearnsetMoveOut.fromJson(Map<String, dynamic>.from(m as Map))],
      ['dragon', 'ground'],
    );
    expect(moves.first.power, isNot(0));
    expect(['dragon', 'ground'], contains(moves.first.type));
    expect(moves.last.power ?? 0, 0);
  });

  testWidgets('opens on Garchomp vs Corviknight and shows the server turn', (tester) async {
    final be = calcBackend();
    await pumpApp(tester, be, location: '/tools/calc');
    await tester.pumpAndSettle();
    final body = lastTurnBody(be);
    final slots = (body['slots']! as List).cast<Map>();
    expect([for (final s in slots) (s['slot'], s['pokemon_id'], s['nature'])], [(0, 445, 'Adamant'), (2, 823, 'Bold')]);
    expect(slots.first['move'], isNotNull);
    expect(body['doubles'], false);
    expect(find.byKey(const Key('hit-0-2')), findsOneWidget);
    expect(find.textContaining('19–22%', findRichText: true), findsWidgets);
    expect(find.textContaining('The opposing', findRichText: true), findsWidgets);
  });

  testWidgets('doubles: spread hits, immunity, a faint and a skipped step', (tester) async {
    final be = calcBackend();
    await pumpApp(tester, be, location: '/tools/calc');
    await tester.pumpAndSettle();
    await _tap(tester, find.text('Doubles'));
    expect(lastTurnBody(be)['doubles'], true);
    expect(find.textContaining("doesn't affect", findRichText: true), findsWidgets);
    expect(find.textContaining('fainted!', findRichText: true), findsWidgets);
    expect(find.textContaining('fainted before it could move', findRichText: true), findsOneWidget);
    expect(find.textContaining('(your partner)', findRichText: true), findsNothing); // immune partner: no damage line
  });

  testWidgets('a Focus Sash save is called out', (tester) async {
    final be = calcBackend(turn: 'turn_sash');
    await pumpApp(tester, be, location: '/tools/calc');
    await tester.pumpAndSettle();
    expect(find.textContaining('hung on using its Focus Sash', findRichText: true), findsOneWidget);
  });

  testWidgets('changing the field asks the server again, and Math shows the terms', (tester) async {
    final be = calcBackend();
    await pumpApp(tester, be, location: '/tools/calc');
    await tester.pumpAndSettle();
    await _tap(tester, find.byKey(const Key('calc-field')));
    await _tap(tester, find.byKey(const Key('weather-Rain')));
    expect((lastTurnBody(be)['field']! as Map)['weather'], 'Rain');
    await _tap(tester, find.byKey(const Key('calc-math')));
    expect(find.byKey(const Key('calc-math-text')), findsOneWidget);
  });

  testWidgets("a stopped server shows the can't-reach state", (tester) async {
    final be = calcBackend()..down = true;
    await pumpApp(tester, be, location: '/tools/calc');
    await tester.pumpAndSettle();
    expect(find.text("Can't reach the server"), findsOneWidget);
  });
}
