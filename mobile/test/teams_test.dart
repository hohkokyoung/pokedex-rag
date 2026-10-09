import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pokerag/api/export.dart';
import 'package:pokerag/features/teams/set_editor.dart';

import 'support/app_harness.dart';
import 'support/fake_backend.dart';
import 'support/teams_backend.dart';

Map<String, Object?> lastBody(FakeBackend be, String method, String path) =>
    Map<String, Object?>.from(be.requests.lastWhere((r) => r.method == method && r.path == path).data as Map);

Future<void> see(WidgetTester tester, Finder f) async {
  await tester.scrollUntilVisible(f, 250, scrollable: find.byType(Scrollable).first);
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('tabs keep their place, and details open over them', (tester) async {
    final router = await pumpApp(tester, teamsBackend());
    await tester.tap(find.byKey(const Key('tab-teams')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Garchomp team'));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('slot-1')), findsOneWidget);
    await tester.tap(find.byKey(const Key('tab-pokedex')));
    await tester.pumpAndSettle();
    expect(find.text('Bulbasaur'), findsOneWidget);
    await tester.tap(find.byKey(const Key('tab-teams')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('slot-1')), findsOneWidget); // still on the team page
    router.push('/pokemon/445');
    await tester.pumpAndSettle();
    expect(find.text('Garchomp'), findsWidgets);
  });

  testWidgets('the team card shows the server rating', (tester) async {
    await pumpApp(tester, teamsBackend(), location: '/teams');
    final card = find.byKey(const Key('team-card-456'));
    expect(find.descendant(of: card, matching: find.text('A')), findsWidgets);
    expect(find.descendant(of: card, matching: find.textContaining('88/100 · Hyper offense')), findsOneWidget);
  });

  testWidgets('New team creates and opens it', (tester) async {
    final be = teamsBackend();
    await pumpApp(tester, be, location: '/teams');
    await tester.tap(find.byKey(const Key('new-team')));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('team-name')), 'Rain');
    await tester.tap(find.byKey(const Key('name-ok')));
    await tester.pumpAndSettle();
    expect(lastBody(be, 'POST', '/api/teams')['name'], 'Rain');
    expect(find.text('Rain'), findsWidgets);
    expect(find.textContaining('Add your first Pokémon'), findsOneWidget);
  });

  testWidgets('Delete asks first; cancel sends nothing', (tester) async {
    final be = teamsBackend();
    await pumpApp(tester, be, location: '/teams');
    await tester.tap(find.byKey(const Key('team-menu-554')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('team-delete')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('delete-cancel')));
    await tester.pumpAndSettle();
    expect(be.requests.where((r) => r.method == 'DELETE'), isEmpty);
    await tester.tap(find.byKey(const Key('team-menu-554')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('team-delete')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('delete-ok')));
    await tester.pumpAndSettle();
    expect(be.requests.last.method, 'GET'); // list reloaded after the DELETE
    expect(be.requests.any((r) => r.method == 'DELETE' && r.path == '/api/teams/554'), isTrue);
    expect(find.text('Rival (mockup)'), findsNothing);
  });

  testWidgets('an empty slot fills from the picker (forms as species + form id)', (tester) async {
    final be = teamsBackend();
    await pumpApp(tester, be, location: '/teams');
    await tester.tap(find.byKey(const Key('new-team')));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('team-name')), 'Sand');
    await tester.tap(find.byKey(const Key('name-ok')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('slot-2')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Bulbasaur'));
    await tester.pumpAndSettle();
    expect(lastBody(be, 'PUT', '/api/teams/900/slots/2')['pokemon_id'], 1);

    // A form: saved as its species (dex 445) + the form id.
    await tester.tap(find.byKey(const Key('slot-3')));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('picker-search')), 'garch');
    await tester.pump(const Duration(milliseconds: 300));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('pick-10058-10058')));
    await tester.pumpAndSettle();
    final form = lastBody(be, 'PUT', '/api/teams/900/slots/3');
    expect(form['pokemon_id'], 445);
    expect(form['form_id'], 10058);
  });

  test('the draft keeps EVs within 252 / 510 and moves within four', () {
    final m = TeamMemberOut.fromJson(((fixture('team_456')! as Map)['members'] as List).first as Map<String, Object?>);
    final d = SetDraft.from(m); // Garchomp: 4 HP / 252 Atk / 252 Spe = 508
    d.setEv('defense', 252);
    expect(d.evTotal, 510);
    expect(d.ev['defense'], 2);
    d.setEv('hp', 400);
    expect(d.ev['hp'], 4); // nothing left of 510 beyond what HP already has
    expect(d.addMove(999, 'Fifth'), isFalse); // already four
    d.moves.removeLast();
    expect(d.addMove(999, 'Fourth'), isTrue);
    final u = d.toUpdate();
    expect(u.moveIds, hasLength(4));
    expect(u.pokemonId, 445);
  });

  testWidgets('the editor saves the whole set, removes, and shows a rejection', (tester) async {
    final be = teamsBackend();
    final router = await pumpApp(tester, be, location: '/teams/456');
    router.push('/teams/456/slot/1');
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('save')));
    await tester.pumpAndSettle();
    final body = lastBody(be, 'PUT', '/api/teams/456/slots/1');
    expect(body['pokemon_id'], 445);
    expect(body['move_ids'], hasLength(4));
    expect((body['ev_spread'] as Map)['attack'], 252);

    router.push('/teams/456/slot/1');
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('remove')));
    await tester.pumpAndSettle();
    expect(be.requests.any((r) => r.method == 'DELETE' && r.path == '/api/teams/456/slots/1'), isTrue);

    final rejecting = teamsBackend(rejectStatus: 422);
    final r2 = await pumpApp(tester, rejecting, location: '/teams/456');
    r2.push('/teams/456/slot/1');
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('save')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('save-error')), findsOneWidget);
  });

  testWidgets('the report shows the server grades and Use suggested fills the gaps', (tester) async {
    final be = teamsBackend();
    await pumpApp(tester, be, location: '/teams/456');
    await see(tester, find.byKey(const Key('rating-line')));
    expect(find.textContaining('88'), findsWidgets);
    await see(tester, find.byKey(const Key('area-defence')));
    expect(find.descendant(of: find.byKey(const Key('area-defence')), matching: find.text('74')), findsOneWidget);
    expect(find.descendant(of: find.byKey(const Key('area-sets')), matching: find.text('61')), findsOneWidget);
    await see(tester, find.byKey(const Key('use-suggested-4')));
    await tester.tap(find.byKey(const Key('use-suggested-4')));
    await tester.pumpAndSettle();
    final build = lastBody(be, 'POST', '/api/teams/456/slots/4/build');
    expect(build['item'], 'Life Orb');
    expect(build['moves'], isNotEmpty);
  });

  testWidgets('compare with Rival shows the matchup; the grade stays opponent-free', (tester) async {
    await pumpApp(tester, teamsBackend(), location: '/teams/456?vs=554');
    await see(tester, find.byKey(const Key('verdict')));
    expect(find.text('Even'), findsOneWidget);
    expect(find.text('17 won'), findsOneWidget);
    expect(find.text('18 won'), findsOneWidget);
    expect(find.textContaining('Tyranitar threatens'), findsOneWidget);
    await see(tester, find.byKey(const Key('rating-line')));
    final line = tester.widget<Text>(find.byKey(const Key('rating-line'))).textSpan!.toPlainText();
    expect(line, startsWith('88/100 · Hyper offense'));
  });
}
