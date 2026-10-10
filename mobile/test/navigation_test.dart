// Moving around the app: pages and the tab bar.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pokerag/features/tools/nature_screen.dart';
import 'package:pokerag/widgets/ui.dart';

import 'support/app_harness.dart';
import 'support/fake_backend.dart';

FakeBackend _backend() => FakeBackend((o) => switch (o.path) {
      '/api/natures' => fixture('natures'),
      '/api/pokemon' => listPage(o),
      _ => 404,
    });

void main() {
  testWidgets('a page sliding in paints its own ground, so the page under it never shows through', (tester) async {
    await pumpApp(tester, _backend(), location: '/tools');
    final before = find.byType(Ground).evaluate().length;
    await tester.tap(find.byKey(const Key('tool-natures')));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 150)); // mid-slide
    // It slides (a page with no transition cuts in with a flash, and can't be swiped back)…
    expect(ModalRoute.of(tester.element(find.byType(NatureScreen)))!.transitionDuration, greaterThan(Duration.zero));
    // …on a ground of its own.
    expect(find.byType(Ground).evaluate().length, greaterThan(before),
        reason: 'the incoming page has an opaque background of its own');
    await tester.pumpAndSettle();
  });

  testWidgets('the tab bar holds four equal tabs, Ask among them, and each switches', (tester) async {
    final router = await pumpApp(tester, _backend());
    final widths = {for (final t in ['pokedex', 'teams', 'tools', 'ask']) tester.getSize(find.byKey(Key('tab-$t'))).width};
    expect(widths, hasLength(1), reason: 'equal widths');
    for (final (t, path) in [('teams', '/teams'), ('tools', '/tools'), ('ask', '/ask'), ('pokedex', '/')]) {
      // The edge of a tab still counts as the tab.
      final r = tester.getRect(find.byKey(Key('tab-$t')));
      await tester.tapAt(r.bottomLeft + const Offset(3, -3));
      await tester.pumpAndSettle();
      expect(router.state.uri.path, path);
    }
  });
}
