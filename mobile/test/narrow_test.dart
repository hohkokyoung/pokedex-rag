// At 375pt (iPhone SE) nothing overflows. Flutter reports any overflow as a test
// failure, and the test font is wider than the real one, so this is stricter than a phone.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'support/app_harness.dart';
import 'support/fake_backend.dart';

const se = Size(375, 667);

FakeBackend be() => FakeBackend((o) => switch (o.path) {
      '/api/pokemon' => listPage(o),
      '/api/pokemon/445' => fixture('garchomp'),
      '/api/pokemon/869' => fixture('alcremie'),
      '/api/types/chart' => fixture('type_chart'),
      '/api/generations' => <Object>[],
      _ => 404,
    });

Future<void> scrollToEnd(WidgetTester tester) async {
  for (var i = 0; i < 12; i++) {
    await tester.drag(find.byType(Scrollable).last, const Offset(0, -500));
    await tester.pumpAndSettle();
  }
}

void main() {
  testWidgets('list at 375pt', (tester) async {
    await pumpApp(tester, be(), size: se);
    expect(find.text('Bulbasaur'), findsOneWidget);
    await scrollToEnd(tester);
  });

  testWidgets('Garchomp at 375pt, every section', (tester) async {
    await pumpApp(tester, be(), size: se, location: '/pokemon/445');
    await scrollToEnd(tester);
    expect(find.text('Evolution'), findsOneWidget);
  });

  testWidgets('Alcremie and its spin guide at 375pt', (tester) async {
    await pumpApp(tester, be(), size: se, location: '/pokemon/869');
    await scrollToEnd(tester);
    expect(find.textContaining('Rules from Pokémon Sword'), findsOneWidget);
  });

  testWidgets('can\'t-reach state at 375pt', (tester) async {
    await pumpApp(tester, be()..down = true, size: se);
    expect(find.text("Can't reach the server"), findsOneWidget);
  });
}
