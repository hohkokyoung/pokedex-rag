import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pokerag/data/server.dart';

import 'support/app_harness.dart';
import 'support/fake_backend.dart';

void main() {
  testWidgets('a stopped server shows the can\'t-reach state, not an empty list', (tester) async {
    final be = FakeBackend((o) => listPage(o))..down = true;
    await pumpApp(tester, be);
    expect(find.text("Can't reach the server"), findsOneWidget);
    expect(find.text(defaultAddress), findsOneWidget);
    expect(find.byKey(const Key('change-address')), findsOneWidget);
    expect(find.text('No Pokémon match.'), findsNothing);

    be.down = false;
    await tester.tap(find.byKey(const Key('retry')));
    await tester.pumpAndSettle();
    expect(find.text('Bulbasaur'), findsOneWidget);
    expect(find.text("Can't reach the server"), findsNothing);
  });

  testWidgets('Change address opens the server setting', (tester) async {
    final be = FakeBackend((o) => listPage(o))..down = true;
    await pumpApp(tester, be);
    await tester.tap(find.byKey(const Key('change-address')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('address')), findsOneWidget);
  });

  testWidgets('the detail page shows it too', (tester) async {
    final be = FakeBackend((o) => fixture('garchomp'))..down = true;
    await pumpApp(tester, be, location: '/pokemon/445');
    expect(find.text("Can't reach the server"), findsOneWidget);
    be.down = false;
    await tester.tap(find.byKey(const Key('retry')));
    await tester.pumpAndSettle();
    expect(find.text('Garchomp'), findsWidgets);
  });
}
