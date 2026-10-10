// The calculator's coach: requests carry the calculator, and cards apply into it only on
// a click (recorded keyless streams; the build proposals are hand-written).
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pokerag/features/tools/calc_screen.dart';
import 'package:pokerag/features/tools/calc_state.dart';

import 'support/app_harness.dart';
import 'support/calc_backend.dart';
import 'support/fake_backend.dart';

Finder get _page => find.byType(Scrollable).first;

Future<void> _show(WidgetTester tester, Finder f) async {
  if (f.evaluate().isEmpty) await tester.scrollUntilVisible(f, 300, scrollable: _page);
  await tester.ensureVisible(f);
  await tester.pumpAndSettle();
}

Future<void> _tap(WidgetTester tester, Finder f) async {
  await _show(tester, f);
  await tester.tap(f);
  await tester.pumpAndSettle();
}

Future<void> _ask(WidgetTester tester, String q) async {
  await _show(tester, find.byKey(const Key('calc-coach-field')));
  await tester.enterText(find.byKey(const Key('calc-coach-field')), q);
  await _tap(tester, find.byKey(const Key('calc-coach-send')));
}

CalcModel _calc(WidgetTester tester) => ProviderScope.containerOf(tester.element(find.byType(CalcScreen))).read(calcProvider);

List<Map<String, Object?>> _asks(FakeBackend be) =>
    [for (final r in be.requests.where((r) => r.path == '/api/calc/ask')) jsonBody(r.data)];

Future<FakeBackend> _open(WidgetTester tester, {Map<String, String> coach = const {}}) async {
  final be = calcBackend(coach: coach);
  await pumpApp(tester, be, location: '/tools/calc');
  await tester.pumpAndSettle();
  return be;
}

void main() {
  testWidgets('a damage question sends the calculator and shows a card, keyless', (tester) async {
    final be = await _open(tester);
    await _tap(tester, find.byKey(const Key('calc-q-Can Garchomp OHKO Corviknight?')));
    final body = _asks(be).single;
    expect(body['question'], 'Can Garchomp OHKO Corviknight?');
    expect(body['focus'], 0);
    expect([for (final s in body['slots']! as List) (s as Map)['slot']], [0, 2]);
    final hits = (body['hits']! as List).cast<Map>();
    expect([for (final h in hits) (h['attacker'], h['target'])], [(0, 2), (2, 0)]);
    expect(body['proposal'], isNull);
    expect(find.byKey(const Key('damage-card-0')), findsOneWidget);
    expect(find.textContaining('0 LLM calls'), findsWidgets);
    expect(find.textContaining('[5]', findRichText: true), findsNothing, reason: 'no sources list here, so no [n]');
  });

  testWidgets('a what-if applies its item into the calculator, and Revert restores it', (tester) async {
    await _open(tester);
    await _ask(tester, 'Can Garchomp OHKO Corviknight with Choice Band?');
    expect(_calc(tester).sets[0].item, 'None', reason: 'nothing changes without a click');
    await _tap(tester, find.byKey(const Key('damage-apply')));
    expect(_calc(tester).sets[0].item, 'Choice Band');
    expect(_calc(tester).sets[0].pre, 'Custom');
    await _tap(tester, find.byKey(const Key('damage-revert')));
    expect(_calc(tester).sets[0].item, 'None');
    expect(_calc(tester).sets[0].pre, 'Offensive');
  });

  testWidgets('a survive card applies EVs and nature; Revert restores the set exactly', (tester) async {
    await _open(tester, coach: {"How much bulk does Garchomp need to survive Corviknight's Sky Attack?": 'calc_survive_needs'});
    final before = _calc(tester).sets[0];
    await _ask(tester, "How much bulk does Garchomp need to survive Corviknight's Sky Attack?");
    await _tap(tester, find.byKey(const Key('survive-apply')));
    final after = _calc(tester).sets[0];
    expect(after.nature, 'Impish');
    expect(after.ev, {'hp': 0, 'atk': 252, 'def': 0, 'spa': 0, 'spd': 0, 'spe': 252});
    await _tap(tester, find.byKey(const Key('survive-revert')));
    final back = _calc(tester).sets[0];
    expect((back.nature, back.ev, back.pre), (before.nature, before.ev, before.pre));
  });

  testWidgets('"already survives" has nothing to apply', (tester) async {
    await _open(tester);
    await _ask(tester, "How much bulk does Garchomp need to survive Corviknight's Sky Attack?");
    expect(find.text('Already survives as set'), findsOneWidget);
    expect(find.byKey(const Key('survive-apply')), findsNothing);
  });

  testWidgets('a build applies set and move; Revert restores both', (tester) async {
    await _open(tester);
    final before = _calc(tester).sets[0];
    await _tap(tester, find.byKey(const Key('calc-q-Best build')));
    expect(find.byKey(const Key('build-card')), findsOneWidget);
    expect(_calc(tester).sets[0].item, before.item, reason: 'nothing changes without a click');
    await _tap(tester, find.byKey(const Key('build-apply')));
    final s = _calc(tester).sets[0];
    expect((s.ability, s.nature, s.item, s.move), ('Rough Skin', 'Jolly', 'Life Orb', 'Earthquake'));
    expect(s.ev['spe'], 252);
    await _tap(tester, find.byKey(const Key('build-revert')));
    final back = _calc(tester).sets[0];
    expect((back.ability, back.nature, back.item, back.move, back.ev), (before.ability, before.nature, before.item, before.move, before.ev));
  });

  testWidgets('a picked moveset chip is the move Apply uses', (tester) async {
    await _open(tester);
    await _tap(tester, find.byKey(const Key('calc-q-Best build')));
    await _tap(tester, find.byKey(const Key('build-move-Dragon Claw')));
    await _tap(tester, find.byKey(const Key('build-apply')));
    expect(_calc(tester).sets[0].move, 'Dragon Claw');
  });

  testWidgets('a revised build waits for Apply; the follow-up carries the proposal', (tester) async {
    final be = await _open(tester);
    await _tap(tester, find.byKey(const Key('calc-q-Best build')));
    await _tap(tester, find.byKey(const Key('build-apply')));
    await _tap(tester, find.byKey(const Key('calc-q-Make it faster')));
    final follow = _asks(be).last;
    final proposal = follow['proposal']! as Map;
    expect((proposal['build'] as Map)['item'], 'Life Orb');
    expect((proposal['thread'] as List).single, {'ask': 'Best build', 'reply': 'A fast Life Orb sweeper: Earthquake and Dragon Claw for STAB.'});
    expect(find.byKey(const Key('build-apply')), findsOneWidget, reason: 'the new build needs its own Apply');
    expect(_calc(tester).sets[0].item, 'Life Orb', reason: 'the applied set stays until then');
  });

  testWidgets('keyless, a build answer says it needs a key and shows no card', (tester) async {
    await _open(tester, coach: {'Best build': 'calc_build_keyless'});
    await _tap(tester, find.byKey(const Key('calc-q-Best build')));
    expect(find.textContaining('need an LLM key', findRichText: true), findsOneWidget);
    expect(find.byKey(const Key('build-card')), findsNothing);
  });
}
