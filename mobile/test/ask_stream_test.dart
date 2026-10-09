import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pokerag/api/export.dart';
import 'package:pokerag/data/server.dart';
import 'package:pokerag/features/ask/ask_state.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'support/fake_backend.dart';

Future<ProviderContainer> containerFor(FakeBackend be) async {
  SharedPreferences.setMockInitialValues({});
  final prefs = await SharedPreferences.getInstance();
  return ProviderContainer.test(overrides: [prefsProvider.overrideWithValue(prefs), httpAdapterProvider.overrideWithValue(be)]);
}

void main() {
  test('a recorded stream builds the whole answer', () async {
    final be = FakeBackend((o) => sse('ask_learn_check'));
    final c = await containerFor(be);
    await c.read(askProvider.notifier).ask('Can Garchomp learn Earthquake?');
    final s = c.read(askProvider);
    final recorded = AskResponse.fromJson(fixture('ask_learn_check')! as Map<String, Object?>);
    expect(s.status, AskStatus.done);
    expect(s.planner, 'keyword');
    expect(s.steps.single.state, 'done');
    expect(s.views.single, isA<LearnCheckView>());
    expect(s.answer, recorded.answer);
    expect(s.sources.map((x) => x.n), recorded.sources.map((x) => x.n));
    expect(s.usage['llm_calls'], 0);
    expect(s.elapsed, isNotNull);
    expect((be.requests.single.data as Map)['question'], 'Can Garchomp learn Earthquake?');
  });

  test('an unknown view kind is skipped, not fatal', () async {
    const stream = 'event: plan\ndata: {"planner":"keyword","cached":false,"replan":false,"steps":[{"id":"s1","tool":"x","why":"w","args":{}}]}\n\n'
        'event: view\ndata: {"kind":"mystery","step":"s1"}\n\n'
        'event: delta\ndata: {"text":"Still here."}\n\n'
        'event: done\ndata: {"usage":{"llm_calls":0},"fallback":false}\n\n';
    final c = await containerFor(FakeBackend((o) => const Raw(stream)));
    await c.read(askProvider.notifier).ask('q');
    final s = c.read(askProvider);
    expect(s.views, isEmpty);
    expect(s.answer, 'Still here.');
    expect(s.status, AskStatus.done);
  });

  test('an error event becomes the error state with its message', () async {
    const stream = 'event: error\ndata: {"message":"Generation failed: boom"}\n\n';
    final c = await containerFor(FakeBackend((o) => const Raw(stream)));
    await c.read(askProvider.notifier).ask('q');
    final s = c.read(askProvider);
    expect(s.status, AskStatus.error);
    expect(s.errorMessage, 'Generation failed: boom');
  });

  test('an unreachable server is reported as such', () async {
    final c = await containerFor(FakeBackend((o) => sse('ask_learn_check'))..down = true);
    await c.read(askProvider.notifier).ask('q');
    expect(isUnreachable(c.read(askProvider).error), isTrue);
  });

  test('the unhandled part of a plan is kept for the notice', () async {
    const stream = 'event: plan\ndata: {"planner":"keyword","cached":false,"replan":false,"unhandled":["cute"],"steps":[]}\n\n'
        'event: done\ndata: {"usage":{},"fallback":false}\n\n';
    final c = await containerFor(FakeBackend((o) => const Raw(stream)));
    await c.read(askProvider.notifier).ask('cute fire types');
    expect(c.read(askProvider).unhandled, ['cute']);
  });
}
