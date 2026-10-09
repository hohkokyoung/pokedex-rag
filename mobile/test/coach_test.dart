// The team coach on the app's team page, over recorded keyless coach streams.
import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pokerag/api/export.dart';
import 'package:pokerag/features/ask/views.dart';
import 'package:pokerag/features/teams/coach_section.dart';

import 'support/app_harness.dart';
import 'support/fake_backend.dart';
import 'support/teams_backend.dart';

Finder get _page => find.byType(Scrollable).first;

Future<void> _show(WidgetTester tester, Finder f) async {
  await tester.scrollUntilVisible(f, 250, scrollable: _page);
  await tester.pumpAndSettle();
}

Future<void> _coach(WidgetTester tester, String q) async {
  await _show(tester, find.byKey(const Key('coach-field')));
  await tester.enterText(find.byKey(const Key('coach-field')), q);
  await _tap(tester, find.byKey(const Key('coach-send')));
}

Future<void> _tap(WidgetTester tester, Finder f) async {
  await tester.ensureVisible(f);
  await tester.pumpAndSettle();
  await tester.tap(f);
  await tester.pumpAndSettle();
}

Iterable<RequestOptions> _writes(FakeBackend be) =>
    be.requests.where((r) => r.method != 'GET' && !r.path.endsWith('/ask'));

void main() {
  test('recorded coach views decode into their cards', () {
    for (final (name, type) in [
      ('coach_set_edit', SetEditView),
      ('coach_draft', CandidatesView),
      ('coach_add', MemberAddedView),
      ('coach_duel', DuelView),
    ]) {
      final view = sse(name).text.split('\n').firstWhere((l) => l.startsWith('data: {"kind"'));
      expect(decodeView(Map<String, dynamic>.from(jsonDecode(view.substring(6)) as Map)).runtimeType, type, reason: name);
    }
  });

  test('quick questions follow the team and the opponent', () {
    final team = TeamOut.fromJson(Map<String, dynamic>.from(fixture('team_456')! as Map));
    final rival = TeamOut.fromJson(Map<String, dynamic>.from(fixture('team_554')! as Map));
    expect(coachQuestions(team, null), [
      "What's my team's biggest weakness?",
      'Which type should I add for coverage?',
      'Give Garchomp its best set',
      'Draft the rest of my team: I like sweepers, non-legendary',
    ]);
    expect(coachQuestions(team, rival)[1], 'How do I beat Rival (mockup)?');
  });

  testWidgets('a plain question streams the server report, with no writes', (tester) async {
    final be = teamsBackend();
    await pumpApp(tester, be, location: '/teams/456');
    await _show(tester, find.byKey(const Key("coach-q-What's my team's biggest weakness?")));
    await _tap(tester, find.byKey(const Key("coach-q-What's my team's biggest weakness?")));
    expect(find.textContaining('overall 19/100'), findsOneWidget);
    expect(find.textContaining('0 LLM calls'), findsWidgets);
    final ask = be.requests.singleWhere((r) => r.path == '/api/teams/456/ask');
    expect(ask.data, {'question': "What's my team's biggest weakness?", 'opponent_id': null});
    expect(_writes(be), isEmpty);
  });

  testWidgets('with an opponent the request carries it', (tester) async {
    final be = teamsBackend();
    await pumpApp(tester, be, location: '/teams/456?vs=554');
    await _show(tester, find.byKey(const Key('coach-field'))); // the opponent loads with the section
    await _show(tester, find.byKey(const Key('coach-q-How do I beat Rival (mockup)?')));
    await _tap(tester, find.byKey(const Key('coach-q-How do I beat Rival (mockup)?')));
    final ask = be.requests.singleWhere((r) => r.path == '/api/teams/456/ask');
    expect((ask.data as Map)['opponent_id'], 554);
  });

  testWidgets('an empty team disables the coach', (tester) async {
    final be = teamsBackend(size456: 0);
    await pumpApp(tester, be, location: '/teams/456');
    await _show(tester, find.byKey(const Key('coach-field')));
    expect(tester.widget<TextField>(find.byKey(const Key('coach-field'))).enabled, isFalse);
    expect(find.text('Add a Pokémon first…'), findsOneWidget);
  });

  testWidgets('a set change saves only on Apply, and Revert restores the member', (tester) async {
    final be = teamsBackend();
    await pumpApp(tester, be, location: '/teams/456');
    await _coach(tester, 'Give Garchomp its best set');
    expect(find.byKey(const Key('set-apply')), findsOneWidget);
    expect(_writes(be), isEmpty, reason: 'nothing saves without a click');

    await _tap(tester, find.byKey(const Key('set-apply')));
    final apply = _writes(be).single;
    expect(apply.path, '/api/teams/456/slots/1/build');
    expect((apply.data as Map)['item'], isNotNull);
    expect(find.byKey(const Key('set-revert')), findsOneWidget);

    await _tap(tester, find.byKey(const Key('set-revert')));
    final revert = _writes(be).last;
    expect(revert.method, 'PUT');
    expect(revert.path, '/api/teams/456/slots/1');
    expect((revert.data as Map)['pokemon_id'], 445);
    expect((revert.data as Map)['move_ids'], isNull); // the recorded Garchomp had no moves set
    expect(find.byKey(const Key('set-apply')), findsOneWidget);
  });

  testWidgets('Dismiss hides a proposal without saving', (tester) async {
    final be = teamsBackend();
    await pumpApp(tester, be, location: '/teams/456');
    await _coach(tester, 'Give Garchomp its best set');
    await _tap(tester, find.byKey(const Key('set-dismiss')));
    expect(find.byKey(const Key('set-apply')), findsNothing);
    expect(_writes(be), isEmpty);
  });

  testWidgets('a candidate Add fills the first empty slot; Revert clears it', (tester) async {
    final be = teamsBackend(size456: 2);
    await pumpApp(tester, be, location: '/teams/456');
    await _coach(tester, 'Draft the rest of my team: I like sweepers, non-legendary');
    final add = find.byKey(const Key('cand-add')).first;
    await _tap(tester, add);
    final put = _writes(be).single;
    expect(put.path, '/api/teams/456/slots/3');
    expect((put.data as Map)['pokemon_id'], isA<int>());
    expect(find.text('Added to slot 3'), findsOneWidget);

    await _tap(tester, find.byKey(const Key('cand-revert')));
    expect(_writes(be).last.method, 'DELETE');
    expect(_writes(be).last.path, '/api/teams/456/slots/3');
  });

  testWidgets('on a full team Replace… → member → Confirm swaps; Revert restores', (tester) async {
    final be = teamsBackend();
    await pumpApp(tester, be, location: '/teams/456');
    await _coach(tester, 'Draft the rest of my team: I like sweepers, non-legendary');
    expect(find.byKey(const Key('cand-add')), findsNothing);
    await _tap(tester, find.byKey(const Key('cand-replace')).first);
    await _tap(tester, find.byKey(const Key('cand-pick-2')));
    expect(_writes(be), isEmpty);
    await _tap(tester, find.byKey(const Key('cand-confirm')));
    expect(_writes(be).single.path, '/api/teams/456/slots/2');

    await _tap(tester, find.byKey(const Key('cand-revert')));
    final restore = _writes(be).last;
    expect(restore.path, '/api/teams/456/slots/2');
    final shuckle = (fixture('team_456')! as Map)['members'] as List;
    final before = shuckle.cast<Map>().firstWhere((m) => m['slot'] == 2);
    expect((restore.data as Map)['pokemon_id'], before['pokemon_id']);
    expect((restore.data as Map)['item_id'], (before['item'] as Map?)?['id']);
    expect((restore.data as Map)['move_ids'], [for (final m in before['moves'] as List) (m as Map)['move_id']]);
  });

  testWidgets('an explicit add refreshes the page and Undo clears the slot', (tester) async {
    final be = teamsBackend(size456: 2);
    await pumpApp(tester, be, location: '/teams/456');
    final before = be.requests.where((r) => r.path == '/api/teams/456' && r.method == 'GET').length;
    await _coach(tester, 'add Dragonite');
    expect(be.requests.where((r) => r.path == '/api/teams/456' && r.method == 'GET').length, greaterThan(before),
        reason: 'team_updated refetches the team');
    expect(find.text('Added Dragonite to slot 3'), findsOneWidget);
    await _tap(tester, find.byKey(const Key('added-undo')));
    expect(_writes(be).single.method, 'DELETE');
    expect(_writes(be).single.path, '/api/teams/456/slots/3');
    expect(find.text('Removed Dragonite again.'), findsOneWidget);
  });

  testWidgets('a duel card shows the outcome and the log', (tester) async {
    await pumpApp(tester, teamsBackend(), location: '/teams/456?vs=554');
    await _coach(tester, 'Duel Garchomp against Blastoise');
    expect(find.byKey(const Key('duel-outcome')), findsOneWidget);
    expect(find.textContaining('Garchomp vs Blastoise'), findsOneWidget);
    expect(find.textContaining('T1'), findsWidgets);
  });

  testWidgets('keyless, a set change says it needs a key', (tester) async {
    await pumpApp(tester, teamsBackend(coach: (b) => sse('coach_set_keyless')), location: '/teams/456');
    await _coach(tester, 'Give Garchomp its best set');
    expect(find.textContaining('need an LLM key'), findsOneWidget);
    expect(find.byKey(const Key('set-apply')), findsNothing);
  });

  testWidgets('a stream error shows in its turn and the coach still asks', (tester) async {
    final be = teamsBackend(coach: (b) => b['question'] == 'fails'
        ? const Raw('event: error\ndata: {"message": "Coaching failed: boom"}\n\n')
        : null);
    await pumpApp(tester, be, location: '/teams/456');
    await _coach(tester, 'fails');
    expect(find.text('Coaching failed: boom'), findsOneWidget);
    await _coach(tester, "What's my team's biggest weakness?");
    expect(find.textContaining('overall 19/100'), findsOneWidget);
  });

  testWidgets('a failed save shows on its card', (tester) async {
    final be = teamsBackend(rejectStatus: 422);
    await pumpApp(tester, be, location: '/teams/456');
    await _coach(tester, 'Give Garchomp its best set');
    await _tap(tester, find.byKey(const Key('set-apply')));
    expect(find.byKey(const Key('coach-card-error')), findsOneWidget);
    expect(find.byKey(const Key('set-apply')), findsOneWidget);
  });
}
