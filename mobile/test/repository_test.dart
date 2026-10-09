import 'package:flutter_test/flutter_test.dart';
import 'package:pokerag/data/errors.dart';
import 'package:pokerag/data/pokedex_repository.dart';

import 'support/fake_backend.dart';

void main() {
  phase2Repo();
  test('pages append without repeats and stop at the end', () async {
    final be = FakeBackend((o) => listPage(o, total: 95));
    final pager = Pager(PokedexRepository(be.dio()), const ListQuery());
    expect(await pager.loadMore(), isTrue);
    expect(pager.items.first.name, 'Bulbasaur');
    await pager.loadMore();
    await pager.loadMore();
    expect(pager.items, hasLength(95));
    expect(pager.items.map((p) => p.id).toSet(), hasLength(95));
    expect(pager.done, isTrue);
    expect(await pager.loadMore(), isFalse);
    expect(be.hits['/api/pokemon'], 3);
  });

  test('the query reaches the backend as filters', () async {
    final be = FakeBackend((o) => listPage(o, total: 0));
    final repo = PokedexRepository(be.dio());
    await repo.page(const ListQuery(q: 'garch', types: ['dragon'], generations: [4], sort: 'speed', descending: true));
    final qp = be.requests.single.queryParameters;
    expect(qp['q'], 'garch');
    expect(qp['type'], ['dragon']);
    expect(qp['generation'], [4]);
    expect(qp['sort'], 'speed');
    expect(qp['order'], 'desc');
  });

  test('the type chart is requested once', () async {
    final be = FakeBackend((o) => fixture('type_chart'));
    final repo = PokedexRepository(be.dio());
    await Future.wait([repo.typeChart(), repo.typeChart()]);
    await repo.typeChart();
    expect(be.hits['/api/types/chart'], 1);
  });

  test('a failed chart fetch is retried next time', () async {
    final be = FakeBackend((o) => fixture('type_chart'))..down = true;
    final repo = PokedexRepository(be.dio());
    await expectLater(repo.typeChart(), throwsA(isA<Unreachable>()));
    be.down = false;
    expect((await repo.typeChart()).order, hasLength(18));
  });

  test('errors map to what the UI shows', () async {
    final be = FakeBackend((o) => 404)..down = true;
    final repo = PokedexRepository(be.dio(baseUrl: 'http://192.168.0.244:8001'));
    await expectLater(
      repo.detail('445'),
      throwsA(isA<Unreachable>().having((u) => u.address, 'address', 'http://192.168.0.244:8001')),
    );
    be.down = false;
    await expectLater(repo.detail('nope'), throwsA(isA<NotFound>()));
    be.handler = (o) => 500;
    await expectLater(repo.detail('445'), throwsA(isA<ServerError>()));
  });
}

void phase2Repo() {
  test('moves, learners, encounters and favourites call the right endpoints', () async {
    final be = FakeBackend((o) => switch (o.path) {
          '/api/pokemon/445/moves/by-game' => fixture('garchomp_moves_swsh'),
          '/api/moves/89/learners/by-game' => fixture('earthquake_learners_sv'),
          '/api/pokemon/445/encounters' => fixture('garchomp_encounters'),
          '/api/profile' || '/api/profile/favorites/445' => fixture('profile'),
          _ => 404,
        });
    final repo = PokedexRepository(be.dio());
    await repo.moves(445, game: 20);
    expect(be.requests.last.queryParameters['version_group'], 20);
    await repo.moves(445);
    expect(be.requests.last.queryParameters.containsKey('version_group'), isFalse);
    await repo.learners(89, game: 25);
    expect(be.requests.last.queryParameters['version_group'], 25);
    await repo.encounters(445, version: 51);
    expect(be.requests.last.queryParameters['version'], 51);
    await repo.addFavourite(445);
    expect(be.requests.last.method, 'POST');
    await repo.removeFavourite(445);
    expect(be.requests.last.method, 'DELETE');
    expect((await repo.profile()).favorites, isNotEmpty);
  });
}
