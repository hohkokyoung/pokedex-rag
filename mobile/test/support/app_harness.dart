import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:pokerag/app.dart';
import 'package:pokerag/data/server.dart';
import 'package:pokerag/widgets/artwork.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'fake_backend.dart';

/// Pumps the whole app against [be], as `main` does (no automatic retries).
Future<GoRouter> pumpApp(WidgetTester tester, FakeBackend be, {String? location, Size size = const Size(390, 844)}) async {
  // A phone-sized screen (iPhone 16/17 points) unless a test asks for another.
  tester.view.physicalSize = size * 3;
  tester.view.devicePixelRatio = 3;
  addTearDown(tester.view.reset);
  SharedPreferences.setMockInitialValues({});
  final prefs = await SharedPreferences.getInstance();
  final router = buildRouter();
  if (location != null) router.go(location);
  await tester.pumpWidget(ProviderScope(
    retry: (_, _) => null,
    overrides: [
      prefsProvider.overrideWithValue(prefs),
      httpAdapterProvider.overrideWithValue(be),
      // Large JSON would decode on another isolate, which a fake-async test never awaits.
      dioTransformerProvider.overrideWithValue(SyncTransformer()),
      // No network images in tests: a sized placeholder that remembers its URL.
      artworkProvider.overrideWithValue((url, size, {fadeIn = Duration.zero}) =>
          SizedBox(key: ValueKey('art:$url'), width: size, height: size)),
    ],
    child: appFor(router),
  ));
  await tester.pumpAndSettle();
  return router;
}

/// Opens a segment of a Pokémon's page (overview, moves, evolution, where).
Future<void> openPart(WidgetTester tester, String part) async {
  final f = find.byKey(Key('part-$part'));
  await tester.ensureVisible(f);
  await tester.pumpAndSettle();
  await tester.tap(f);
  await tester.pumpAndSettle();
}

/// Lets a request started on the last settled frame finish (a refetch can begin on a
/// frame that schedules no other; with no tap ripples left, nothing else keeps frames going).
Future<void> flush(WidgetTester tester) async {
  await tester.pump();
  await tester.pumpAndSettle();
}
