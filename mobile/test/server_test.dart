import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:pokerag/data/server.dart';
import 'package:pokerag/features/settings/settings_screen.dart';
import 'package:pokerag/theme/theme.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'support/fake_backend.dart';

const home = 'http://192.168.0.244:8001';

FakeBackend healthyAt(Set<String> addresses) =>
    FakeBackend((o) => o.path == '/health' ? {'status': 'ok'} : listPage(o))..reachableAt = addresses;

Future<ProviderContainer> containerWith(FakeBackend be, {Map<String, Object> saved = const {}}) async {
  SharedPreferences.setMockInitialValues(saved);
  final prefs = await SharedPreferences.getInstance();
  return ProviderContainer.test(overrides: [
    prefsProvider.overrideWithValue(prefs),
    httpAdapterProvider.overrideWithValue(be),
  ]);
}

Future<void> pumpSettings(WidgetTester tester, ProviderContainer c) async {
  final router = GoRouter(routes: [
    GoRoute(path: '/', builder: (_, _) => const Text('list')),
    GoRoute(path: '/settings', builder: (_, _) => const SettingsScreen()),
  ], initialLocation: '/settings');
  await tester.pumpWidget(UncontrolledProviderScope(
    container: c,
    child: MaterialApp.router(theme: AppTheme.light(), routerConfig: router),
  ));
}

void main() {
  test('addresses are normalised', () {
    expect(normalize('192.168.0.244:8001'), home);
    expect(normalize(' http://192.168.0.244:8001/ '), home);
    expect(normalize('not a url'), isNull);
    expect(normalize(''), isNull);
  });

  test('the build default is used until an address is saved', () async {
    final c = await containerWith(healthyAt({defaultAddress}));
    expect(c.read(serverAddressProvider), defaultAddress);
    expect(c.read(repositoryProvider).address, defaultAddress);
  });

  testWidgets('a wrong address is not saved and says why', (tester) async {
    final c = await containerWith(healthyAt({home}));
    await pumpSettings(tester, c);
    await tester.enterText(find.byKey(const Key('address')), 'http://10.9.9.9:8001');
    await tester.tap(find.byKey(const Key('save')));
    await tester.pumpAndSettle();
    expect(find.textContaining("Couldn't reach a pokérag server at http://10.9.9.9:8001"), findsOneWidget);
    expect(c.read(serverAddressProvider), defaultAddress);
    expect(c.read(prefsProvider).getString('server_address'), isNull);
  });

  testWidgets('something that is not pokérag is not saved', (tester) async {
    final be = FakeBackend((o) => {'hello': 'world'});
    final c = await containerWith(be);
    await pumpSettings(tester, c);
    await tester.enterText(find.byKey(const Key('address')), home);
    await tester.tap(find.byKey(const Key('save')));
    await tester.pumpAndSettle();
    expect(find.textContaining("isn't a pokérag server"), findsOneWidget);
    expect(c.read(serverAddressProvider), defaultAddress);
  });

  testWidgets('a right address is saved and the data source switches to it', (tester) async {
    final c = await containerWith(healthyAt({home}));
    await pumpSettings(tester, c);
    await tester.enterText(find.byKey(const Key('address')), '192.168.0.244:8001');
    await tester.tap(find.byKey(const Key('save')));
    await tester.pumpAndSettle();
    expect(c.read(serverAddressProvider), home);
    expect(c.read(repositoryProvider).address, home);
    expect(find.text('list'), findsOneWidget); // back to the list, which reloads from the new server
  });

  test('a saved address survives a restart', () async {
    final c = await containerWith(healthyAt({home}), saved: {'server_address': home});
    expect(c.read(serverAddressProvider), home);
  });
}
