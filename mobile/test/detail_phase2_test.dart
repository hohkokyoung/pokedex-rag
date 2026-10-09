import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'support/app_harness.dart';
import 'support/fake_backend.dart';

FakeBackend be({bool favouritesFail = false}) {
  final favs = <Map<String, Object?>>[];
  late FakeBackend b;
  b = FakeBackend((o) {
    Map<String, Object?> profile() => {'preferred_types': <String>[], 'favorites': favs};
    switch (o.path) {
      case '/api/pokemon/445':
        return fixture('garchomp');
      case '/api/pokemon/446':
        return {...(fixture('garchomp')! as Map<String, Object?>), 'id': 446, 'dex_number': 446, 'name': 'Munchlax', 'forms': <Object>[]};
      case '/api/pokemon/1':
        return {...(fixture('garchomp')! as Map<String, Object?>), 'id': 1, 'dex_number': 1, 'name': 'Bulbasaur', 'forms': <Object>[]};
      case '/api/pokemon/81':
        return fixture('magnemite');
      case '/api/types/chart':
        return fixture('type_chart');
      case '/api/pokemon':
        return listPage(o, total: 1025);
      case '/api/pokemon/445/moves/by-game':
        return fixture(o.queryParameters['version_group'] == 20 ? 'garchomp_moves_swsh' : 'garchomp_moves_sv');
      case '/api/moves/89/learners/by-game':
        return fixture('earthquake_learners_sv');
      case '/api/pokemon/445/encounters':
        return fixture('garchomp_encounters');
      case '/api/profile':
        return profile();
      case '/api/profile/favorites/445':
        if (favouritesFail) return 500;
        if (o.method == 'POST') {
          favs.add({'id': 445, 'dex_number': 445, 'name': 'Garchomp', 'types': ['dragon', 'ground'], 'sprite_url': '/x.png'});
        } else {
          favs.removeWhere((f) => f['id'] == 445);
        }
        return profile();
    }
    if (o.path.endsWith('/moves/by-game')) return {'version_group_id': null, 'games': <Object>[], 'moves': <Object>[]};
    if (o.path.endsWith('/encounters')) return {'version_id': null, 'games': <Object>[], 'encounters': <Object>[]};
    return 404;
  });
  return b;
}

Future<void> see(WidgetTester tester, Finder f) async {
  await tester.scrollUntilVisible(f, 250, scrollable: find.byType(Scrollable).first);
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('facts and training & breeding', (tester) async {
    await pumpApp(tester, be(), location: '/pokemon/445');
    await see(tester, find.text('Base friendship'));
    for (final t in ['1.9 m', '95.0 kg', 'Monster, Dragon', '40 cycles · ~10,455 steps', 'Slow', '3 Attack', '45']) {
      expect(find.text(t), findsWidgets, reason: t);
    }
    expect(find.textContaining('♂ 50%'), findsOneWidget);
  });

  testWidgets('a genderless Pokémon reads Genderless', (tester) async {
    await pumpApp(tester, be(), location: '/pokemon/81');
    await see(tester, find.text('Genderless'));
  });

  testWidgets('moveset: Evo, TM labels, game switch and filters', (tester) async {
    final b = be();
    await pumpApp(tester, b, location: '/pokemon/445');
    await see(tester, find.byKey(const Key('moveset-game')));
    await see(tester, find.byKey(const Key('move-242-level-up')));
    expect(find.descendant(of: find.byKey(const Key('move-242-level-up')), matching: find.text('Evo')), findsOneWidget);
    await see(tester, find.byKey(const Key('move-89-machine')));
    expect(find.descendant(of: find.byKey(const Key('move-89-machine')), matching: find.text('TM149')), findsOneWidget);

    await see(tester, find.byKey(const Key('cat-special')));
    await tester.tap(find.byKey(const Key('cat-special')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('move-89-machine')), findsNothing); // Earthquake is physical

    await see(tester, find.byKey(const Key('moveset-game')));
    await tester.tap(find.byKey(const Key('moveset-game')));
    await tester.pumpAndSettle();
    await tester.tap(find.textContaining('Sword / Shield').last);
    await tester.pumpAndSettle();
    expect(b.requests.lastWhere((r) => r.path == '/api/pokemon/445/moves/by-game').queryParameters['version_group'], 20);
  });

  testWidgets('a move opens its learners, and a learner opens its page', (tester) async {
    await pumpApp(tester, be(), location: '/pokemon/445');
    await see(tester, find.byKey(const Key('move-89-machine')));
    await tester.tap(find.byKey(const Key('move-89-machine')));
    await tester.pumpAndSettle();
    expect(find.text('Earthquake'), findsWidgets);
    expect(find.textContaining('Power 100'), findsOneWidget);
    await tester.scrollUntilVisible(find.byKey(const Key('learner-389')), 200, scrollable: find.byType(Scrollable).last);
    await tester.tap(find.byKey(const Key('learner-389')));
    await tester.pumpAndSettle();
    // Torterra (#389) isn't in this fake backend, so its page says so: the route was followed.
    expect(find.textContaining('No Pokémon “389”'), findsOneWidget);
  });

  testWidgets('dex entries by generation and where to find', (tester) async {
    await pumpApp(tester, be(), location: '/pokemon/445');
    await see(tester, find.text('Gen IV'));
    await see(tester, find.text('Ballimere Lake · Max Den Q'));
    expect(find.textContaining('Max Raid · Lv 45–60'), findsWidgets);
  });

  testWidgets('favourite on and off, and the Favourites screen', (tester) async {
    final b = be();
    final router = await pumpApp(tester, b, location: '/pokemon/445');
    await tester.tap(find.byKey(const Key('favourite')));
    await tester.pumpAndSettle();
    expect(b.requests.last.method, 'POST');
    expect(find.byIcon(Icons.favorite), findsOneWidget);
    router.push('/favourites');
    await tester.pumpAndSettle();
    expect(find.text('Garchomp'), findsOneWidget);
    router.pop();
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('favourite')));
    await tester.pumpAndSettle();
    expect(b.requests.last.method, 'DELETE');
    expect(find.byIcon(Icons.favorite_border), findsOneWidget);
  });

  testWidgets('a failed favourite reverts the heart', (tester) async {
    await pumpApp(tester, be(favouritesFail: true), location: '/pokemon/445');
    await tester.tap(find.byKey(const Key('favourite')));
    await tester.pumpAndSettle();
    expect(find.byIcon(Icons.favorite_border), findsOneWidget);
    expect(find.textContaining("Couldn't update favourites"), findsOneWidget);
  });

  testWidgets('previous and next move by dex number', (tester) async {
    await pumpApp(tester, be(), location: '/pokemon/445');
    await tester.tap(find.byKey(const Key('next')));
    await tester.pumpAndSettle();
    expect(find.text('Munchlax'), findsWidgets);
    await pumpApp(tester, be(), location: '/pokemon/1');
    expect(find.byKey(const Key('prev')), findsNothing);
    expect(find.byKey(const Key('next')), findsOneWidget);
  });
}
