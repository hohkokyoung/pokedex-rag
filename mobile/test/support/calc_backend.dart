// The damage calculator's fake server: recorded Garchomp / Corviknight data, the turns
// POST /api/calc/turn returned, and the calc coach's recorded streams.
import 'dart:convert';

import 'fake_backend.dart';

/// The coach's recorded streams (test/fixtures/calc_*.sse) by question.
const calcCoachRecorded = {
  'Can Garchomp OHKO Corviknight?': 'calc_damage',
  'Can Garchomp OHKO Corviknight with Choice Band?': 'calc_whatif',
  "How much bulk does Garchomp need to survive Corviknight's Sky Attack?": 'calc_survive',
  'Best build': 'calc_build',
  'Make it faster': 'calc_build_faster',
};

FakeBackend calcBackend({String? turn, Map<String, String> coach = const {}}) => FakeBackend((o) {
      final body = jsonBody(o.data);
      if (o.path == '/api/calc/ask') {
        final name = coach[body['question']] ?? calcCoachRecorded[body['question']];
        return name == null ? 404 : sse(name);
      }
      return switch (o.path) {
        '/api/pokemon/445' => fixture('garchomp'),
        '/api/pokemon/823' => fixture('corviknight'),
        '/api/pokemon/445/moves' => fixture('learnset_445'),
        '/api/pokemon/823/moves' => fixture('learnset_823'),
        '/api/pokemon/445/abilities' => fixture('abilities_445'),
        '/api/pokemon/823/abilities' => fixture('abilities_823'),
        '/api/calc/options' => fixture('calc_options'),
        '/api/calc/turn' => fixture(turn ??
            (body['doubles'] == true
                ? 'turn_doubles'
                : ((body['slots'] as List?) ?? const []).any((s) => (s as Map)['item'] == 'Focus Sash')
                    ? 'turn_sash'
                    : 'turn_default')),
        '/api/pokemon' => listPage(o),
        _ => 404,
      };
    });

/// A request body as it goes over the wire (Dio serializes generated models later).
Map<String, Object?> jsonBody(Object? data) => data is Map ? Map<String, Object?>.from(jsonDecode(jsonEncode(data)) as Map) : const {};

Map<String, Object?> lastTurnBody(FakeBackend be) => jsonBody(be.requests.lastWhere((r) => r.path == '/api/calc/turn').data);
