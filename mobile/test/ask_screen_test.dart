import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'support/app_harness.dart';
import 'support/fake_backend.dart';

const recorded = {
  'Can Garchomp learn Earthquake?': 'ask_learn_check',
  'What is Fire weak to?': 'ask_type_chart',
  'Which Pokémon has the highest Attack?': 'ask_ranking',
  'Which Fire types learn Will-O-Wisp, and what is Fire weak to?': 'ask_multi',
  'What moves does Pikachu learn?': 'ask_learnset',
  'What does Earthquake do?': 'ask_move',
  'Tell me about Snorlax': 'ask_about',
};

FakeBackend askBackend({bool enabled = false}) {
  var preferred = <String>[];
  return FakeBackend((o) {
    switch (o.path) {
      case '/api/ask/stream':
        final q = (o.data as Map)['question'] as String;
        if (q == 'unhandled') {
          // The ranking stream with a part of the question the plan couldn't apply.
          return Raw(sse('ask_ranking').text.replaceFirst('"replan": false,', '"replan": false, "unhandled": ["shiny only"],'));
        }
        if (q == 'fails') {
          return const Raw('event: plan\ndata: {"planner": "keyword", "cached": false, "replan": false, "steps": []}\n\n'
              'event: error\ndata: {"message": "The lookup failed."}\n\n');
        }
        return sse(recorded[q] ?? 'ask_about');
      case '/api/ask/status':
        return {'enabled': enabled, 'provider': enabled ? 'groq' : 'none'};
      case '/api/types/chart':
        return fixture('type_chart');
      case '/api/profile':
        if (o.method == 'PUT') preferred = ((o.data as Map)['preferred_types'] as List).cast<String>();
        return {'preferred_types': preferred, 'favorites': <Object>[]};
      case '/api/pokemon':
        return listPage(o);
    }
    return 404;
  });
}

Future<void> ask(WidgetTester tester, String q) async {
  await tester.enterText(find.byKey(const Key('ask-field')), q);
  await tester.tap(find.byKey(const Key('ask-send')));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('starters, keyless status, and a starter asks', (tester) async {
    await pumpApp(tester, askBackend(), location: '/ask');
    for (final k in ['Rank', 'Lore', 'Multi', 'Matchup', 'For you']) {
      expect(find.byKey(Key('starter-$k')), findsOneWidget);
    }
    expect(find.textContaining('Keyless'), findsOneWidget);
    await tester.tap(find.byKey(const Key('starter-Rank')));
    await tester.pumpAndSettle();
    expect(find.textContaining('Kartana'), findsWidgets);
    expect(find.textContaining('Highest Attack'), findsOneWidget); // the ranking card
  });

  testWidgets('a learn check: verdict card, answer, and the How line', (tester) async {
    await pumpApp(tester, askBackend(), location: '/ask');
    await ask(tester, 'Can Garchomp learn Earthquake?');
    expect(find.byKey(const Key('learn-verdict')), findsOneWidget);
    expect(find.textContaining('Yes'), findsWidgets);
    expect(find.textContaining('Planned by keywords'), findsOneWidget);
    expect(find.textContaining('0 LLM calls'), findsOneWidget);
  });

  testWidgets('tapping a citation opens its record', (tester) async {
    await pumpApp(tester, askBackend(), location: '/ask');
    await ask(tester, 'Can Garchomp learn Earthquake?');
    // The first [n] in the card's "From" line.
    // The page's list (the multi-line question box is a Scrollable too).
    final page = find.ancestor(of: find.byKey(const Key('how-answered')), matching: find.byType(Scrollable)).first;
    await tester.scrollUntilVisible(find.text('[1]'), 200, scrollable: page);
    await tester.tap(find.text('[1]').last);
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('source-snippet')), findsOneWidget);
    expect(find.byKey(const Key('source-open')), findsOneWidget);
  });

  testWidgets('every Ask view kind renders a card', (tester) async {
    await pumpApp(tester, askBackend(), location: '/ask');
    final expectTitle = {
      'What is Fire weak to?': 'Fire matchups',
      'Which Fire types learn Will-O-Wisp, and what is Fire weak to?': 'learn Will-O-Wisp',
      'What moves does Pikachu learn?': 'Pikachu',
      'What does Earthquake do?': 'Earthquake',
      'Tell me about Snorlax': 'Snorlax',
    };
    for (final MapEntry(key: q, value: title) in expectTitle.entries) {
      await ask(tester, q);
      expect(find.textContaining(title), findsWidgets, reason: q);
    }
  });

  testWidgets('follow-ups come from the cited Pokémon', (tester) async {
    await pumpApp(tester, askBackend(), location: '/ask');
    await ask(tester, 'Can Garchomp learn Earthquake?');
    expect(find.byKey(const Key('next-Tell me about Garchomp')), findsOneWidget);
    expect(find.byKey(const Key('next-What is similar to Garchomp?')), findsOneWidget);
  });

  testWidgets('the profile sheet sets preferred types on the server', (tester) async {
    final be = askBackend();
    await pumpApp(tester, be, location: '/ask');
    await tester.tap(find.byKey(const Key('open-profile')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('pref-dragon')));
    await tester.pumpAndSettle();
    final put = be.requests.lastWhere((r) => r.method == 'PUT' && r.path == '/api/profile');
    expect((put.data as Map)['preferred_types'], ['dragon']);
  });

  testWidgets('an unreachable server shows the can\'t-reach state', (tester) async {
    final be = askBackend();
    await pumpApp(tester, be, location: '/ask');
    be.down = true;
    await ask(tester, 'Can Garchomp learn Earthquake?');
    expect(find.text("Can't reach the server"), findsOneWidget);
  });

  testWidgets("a part the plan couldn't apply is said up front", (tester) async {
    await pumpApp(tester, askBackend(), location: '/ask');
    await ask(tester, 'unhandled');
    expect(find.byKey(const Key('ask-notice')), findsOneWidget);
    expect(find.textContaining('shiny only'), findsOneWidget);
  });

  testWidgets('a stream error shows its message, not a blank answer', (tester) async {
    await pumpApp(tester, askBackend(), location: '/ask');
    await ask(tester, 'fails');
    expect(find.byKey(const Key('ask-error')), findsOneWidget);
    expect(find.text('The lookup failed.'), findsOneWidget);
  });

  testWidgets('a card lists its sources and opens its Pokémon', (tester) async {
    final router = await pumpApp(tester, askBackend(), location: '/ask');
    await ask(tester, 'Which Pokémon has the highest Attack?');
    final page = find.ancestor(of: find.byKey(const Key('how-answered')), matching: find.byType(Scrollable)).first;
    await tester.scrollUntilVisible(find.text('From '), 200, scrollable: page);
    expect(find.text('From '), findsOneWidget);
    final row = find.text('Kartana').last;
    await tester.ensureVisible(row);
    await tester.pumpAndSettle();
    await tester.tap(row);
    await tester.pumpAndSettle();
    expect(router.state.uri.path, '/pokemon/798');
  });
}
