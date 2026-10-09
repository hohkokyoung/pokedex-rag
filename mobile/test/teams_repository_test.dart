import 'package:flutter_test/flutter_test.dart';
import 'package:pokerag/api/export.dart';
import 'package:pokerag/data/errors.dart';
import 'package:pokerag/data/teams_repository.dart';

import 'support/fake_backend.dart';

void main() {
  test('writes send the right method, path and body', () async {
    final be = FakeBackend((o) => switch ((o.method, o.path)) {
          ('POST', '/api/teams') => fixture('team_456'),
          ('PUT', '/api/teams/456') => fixture('team_456'),
          ('DELETE', '/api/teams/456') => '',
          ('PUT', '/api/teams/456/slots/2') => fixture('team_456'),
          ('DELETE', '/api/teams/456/slots/2') => fixture('team_456'),
          ('POST', '/api/teams/456/slots/2/build') => fixture('team_456'),
          ('GET', '/api/teams/456/analysis') => fixture('analysis_456_vs_554'),
          _ => 404,
        });
    final repo = TeamsRepository(be.dio());
    await repo.create('Rain');
    expect(be.requests.last.data, containsPair('name', 'Rain'));
    await repo.rename(456, 'Sand');
    expect((be.requests.last.data as Map)['name'], 'Sand');
    await repo.delete(456);
    expect(be.requests.last.method, 'DELETE');
    await repo.setSlot(456, 2, const SlotUpdate(pokemonId: 445, moveIds: [89, 200]));
    final body = be.requests.last.data as Map;
    expect(body['pokemon_id'], 445);
    expect(body['move_ids'], [89, 200]);
    await repo.clearSlot(456, 2);
    expect(be.requests.last.path, '/api/teams/456/slots/2');
    await repo.applyBuild(456, 2, const SlotBuild(moves: ['Earthquake'], nature: 'Jolly'));
    expect((be.requests.last.data as Map)['nature'], 'Jolly');
    await repo.analysis(456, opponentId: 554);
    expect(be.requests.last.queryParameters['opponent_id'], 554);
  });

  test('a 422 surfaces the server\'s reason', () async {
    final be = FakeBackend((o) => 422);
    final repo = TeamsRepository(be.dio());
    await expectLater(repo.setSlot(1, 1, const SlotUpdate(pokemonId: 1)), throwsA(isA<Rejected>()));
  });
}
