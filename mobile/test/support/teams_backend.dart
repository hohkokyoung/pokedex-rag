// A fake pokérag server with teams: the recorded Garchomp team (456) and Rival (554),
// plus teams created during a test. Writes are recorded in `requests`.
import 'package:dio/dio.dart';

import 'fake_backend.dart';

Map<String, Object?> _j(String n) => Map<String, Object?>.from(fixture(n)! as Map);

/// The coach's recorded keyless streams (test/fixtures/coach_*.sse) by question.
const coachRecorded = {
  "What's my team's biggest weakness?": 'coach_plain',
  'Draft the rest of my team: I like sweepers, non-legendary': 'coach_draft',
  'Give Garchomp its best set': 'coach_set_edit',
  'Give Garchomp its best set (keyless)': 'coach_set_keyless',
  'How do I beat Rival (mockup)?': 'coach_vs',
  'Duel Garchomp against Blastoise': 'coach_duel',
  'add Dragonite': 'coach_add',
};

/// [size456] keeps only that many of the Garchomp team's members (so Add has a slot).
FakeBackend teamsBackend({int? rejectStatus, int? size456, Object? Function(Map body)? coach}) {
  final teams = <int, Map<String, Object?>>{456: _j('team_456'), 554: _j('team_554')};
  if (size456 != null) (teams[456]!['members']! as List).removeRange(size456, (teams[456]!['members']! as List).length);
  var nextId = 900;
  Map<String, Object?> summaryOf(Map<String, Object?> t) {
    final members = (t['members']! as List).cast<Map>();
    return {
      'id': t['id'],
      'name': t['name'],
      'kind': 'player',
      'size': members.length,
      'sprites': [for (final m in members) m['sprite_url']],
    };
  }

  Object? handle(RequestOptions o) {
    final p = o.path;
    final m = o.method;
    if (p == '/api/teams' && m == 'GET') return {'teams': [for (final t in teams.values) summaryOf(t)]};
    if (p == '/api/teams' && m == 'POST') {
      final id = nextId++;
      teams[id] = {'id': id, 'name': (o.data as Map)['name'], 'kind': 'player', 'notes': null, 'members': <Object>[]};
      return teams[id];
    }
    final team = RegExp(r'^/api/teams/(\d+)').firstMatch(p);
    if (team != null) {
      final id = int.parse(team[1]!);
      final t = teams[id];
      if (t == null) return 404;
      final rest = p.substring(team[0]!.length);
      if (rest == '' && m == 'GET') return t;
      if (rest == '' && m == 'PUT') return t..['name'] = (o.data as Map)['name'] ?? t['name'];
      if (rest == '' && m == 'DELETE') {
        teams.remove(id);
        return '';
      }
      if (rest == '/analysis') {
        if (id == 456) return _j(o.queryParameters['opponent_id'] == 554 ? 'analysis_456_vs_554' : 'analysis_456');
        if (id == 554) return _j('analysis_554');
        return {..._j('analysis_456'), 'team_id': id, 'rating': null, 'profile': null, 'size': 0};
      }
      if (rest == '/ask' && m == 'POST') {
        final body = o.data as Map;
        final custom = coach?.call(body);
        if (custom != null) return custom;
        final name = coachRecorded[body['question']];
        if (name == null) return 404;
        // The recordings used team 1 and opponent 2.
        return Raw(sse(name).text.replaceAll('"team_id": 1', '"team_id": $id').replaceAll('"opponent_id": 2', '"opponent_id": ${body['opponent_id'] ?? 554}'));
      }
      if (rest == '/strategy') return _j(id == 554 ? 'strategy_554' : 'strategy_456');
      if (rest == '/summary') return {'team_id': id, 'text': 'A test summary.', 'source': 'rules', 'pending': false};
      if (rest == '/summary/refresh') return {'team_id': id, 'text': 'Fresh.', 'source': 'ai', 'pending': false};
      final slot = RegExp(r'^/slots/(\d)(/build)?$').firstMatch(rest);
      if (slot != null) {
        if (rejectStatus != null) return rejectStatus;
        final s = int.parse(slot[1]!);
        final members = (t['members']! as List).cast<Map<String, Object?>>();
        if (m == 'DELETE') {
          members.removeWhere((x) => x['slot'] == s);
        } else if (slot[2] == null && m == 'PUT') {
          final body = o.data as Map;
          members.removeWhere((x) => x['slot'] == s);
          final from = (_j('team_456')['members']! as List).cast<Map<String, Object?>>().first;
          members.add({...from, 'slot': s, 'pokemon_id': body['pokemon_id'], 'form_id': body['form_id']});
        }
        return t;
      }
    }
    return switch (p) {
      '/api/pokemon' => fixture(o.queryParameters['q'] == 'garch' ? 'list_garch' : 'list_page1'),
      '/api/pokemon/445' => fixture('garchomp'),
      '/api/pokemon/445/abilities' => fixture('abilities_445'),
      '/api/pokemon/445/moves' => fixture('learnset_445'),
      '/api/natures' => fixture('natures'),
      '/api/items' => fixture('items_scarf'),
      '/api/types/chart' => fixture('type_chart'),
      _ => 404,
    };
  }

  return FakeBackend(handle);
}
