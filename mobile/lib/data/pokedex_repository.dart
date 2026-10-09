import 'package:dio/dio.dart';

import '../api/export.dart';
import 'errors.dart';

/// What the list shows: every change resets paging to the first page.
class ListQuery {
  const ListQuery({
    this.q = '',
    this.types = const [],
    this.generations = const [],
    this.sort = 'dex',
    this.descending = false,
  });

  final String q;
  final List<String> types; // up to 2; all must match
  final List<int> generations; // any may match
  final String sort; // dex | name | total | hp | attack | defense | sp_attack | sp_defense | speed
  final bool descending;

  bool get isFiltered => q.isNotEmpty || types.isNotEmpty || generations.isNotEmpty;

  ListQuery copyWith({String? q, List<String>? types, List<int>? generations, String? sort, bool? descending}) =>
      ListQuery(
        q: q ?? this.q,
        types: types ?? this.types,
        generations: generations ?? this.generations,
        sort: sort ?? this.sort,
        descending: descending ?? this.descending,
      );

  @override
  bool operator ==(Object other) =>
      other is ListQuery &&
      other.q == q &&
      _same(other.types, types) &&
      _same(other.generations, generations) &&
      other.sort == sort &&
      other.descending == descending;

  @override
  int get hashCode => Object.hash(q, Object.hashAll(types), Object.hashAll(generations), sort, descending);

  static bool _same<T>(List<T> a, List<T> b) => a.length == b.length && Iterable.generate(a.length).every((i) => a[i] == b[i]);
}

class Page {
  const Page(this.items, this.total);
  final List<PokemonSummary> items;
  final int total;
}

/// Reads the Pokédex from the backend. The type chart is fetched once per repository
/// (one per launch and server address) and reused.
class PokedexRepository {
  PokedexRepository(this._dio) : _api = PokeragClient(_dio);

  static const pageSize = 40;

  final Dio _dio;
  final PokeragClient _api;
  Future<TypeChartOut>? _chart;

  String get address => _dio.options.baseUrl;

  Future<Page> page(ListQuery query, {int offset = 0}) => _guard(() async {
        final r = await _api.listPokemonApiPokemonGet(
          q: query.q.isEmpty ? null : query.q,
          type: query.types.isEmpty ? null : query.types,
          generation: query.generations.isEmpty ? null : query.generations,
          sort: query.sort,
          order: query.descending ? 'desc' : 'asc',
          limit: pageSize,
          offset: offset,
        );
        return Page(r.items, r.total);
      });

  /// How many species the dex has (bounds previous / next).
  Future<int> dexTotal() => _guard(() async => (await _api.listPokemonApiPokemonGet(limit: 1)).total);

  Future<PokemonDetail> detail(String idOrName) => _guard(() => _api.getPokemonApiPokemonIdOrNameGet(idOrName: idOrName));

  Future<List<TypeOut>> types() => _guard(_api.listTypesApiTypesGet);

  Future<List<GenerationOut>> generations() => _guard(_api.listGenerationsApiGenerationsGet);

  /// A species' or form's (id > 10000) moves in one game; null game = the newest.
  Future<PokemonGameMovesOut> moves(int pokemonId, {int? game}) => _guard(
        () => _api.pokemonMovesByGameApiPokemonPokemonIdMovesByGameGet(pokemonId: pokemonId, versionGroup: game),
      );

  /// Who learns a move in one game; null game = every game.
  Future<MoveGameLearnersOut> learners(int moveId, {int? game}) => _guard(
        () => _api.moveLearnersByGameApiMovesMoveIdLearnersByGameGet(moveId: moveId, versionGroup: game),
      );

  /// Where to find a Pokémon in one game (version); null = the newest it appears in.
  Future<PokemonEncountersOut> encounters(int pokemonId, {int? version}) => _guard(
        () => _api.pokemonEncountersApiPokemonPokemonIdEncountersGet(pokemonId: pokemonId, version: version),
      );

  /// The server profile (favourites), shared with the website and Ask.
  Future<ProfileOut> profile() => _guard(_api.getProfileApiProfileGet);
  Future<ProfileOut> addFavourite(int pokemonId) =>
      _guard(() => _api.addFavoriteApiProfileFavoritesPokemonIdPost(pokemonId: pokemonId));
  Future<ProfileOut> removeFavourite(int pokemonId) =>
      _guard(() => _api.removeFavoriteApiProfileFavoritesPokemonIdDelete(pokemonId: pokemonId));

  /// The served type chart, requested at most once; a failed request is retried next time.
  Future<TypeChartOut> typeChart() => _chart ??= _guard(_api.typeChartApiTypesChartGet).catchError((Object e) {
        _chart = null;
        throw e;
      });

  Future<T> _guard<T>(Future<T> Function() call) async {
    try {
      return await call();
    } on DioException catch (e) {
      throw failureOf(e, address);
    }
  }
}

/// Maps a dio error to what the UI shows.
ApiFailure failureOf(DioException e, String address) {
  switch (e.type) {
    case DioExceptionType.connectionError:
    case DioExceptionType.connectionTimeout:
    case DioExceptionType.sendTimeout:
    case DioExceptionType.receiveTimeout:
      return Unreachable(address);
    case DioExceptionType.badResponse:
      final status = e.response?.statusCode;
      return status == 404 ? const NotFound() : ServerError(status);
    default:
      // Socket errors before a response (e.g. "connection refused") land here too.
      return e.response == null ? Unreachable(address) : ServerError(e.response!.statusCode);
  }
}

/// The list's paging state for one query: appends pages, never repeats a Pokémon,
/// and knows when it has everything.
class Pager {
  Pager(this.repo, this.query);

  final PokedexRepository repo;
  final ListQuery query;
  final List<PokemonSummary> items = [];
  final Set<String> _seen = {};
  int? total;
  bool _loading = false;

  bool get done => total != null && (items.length >= total! || _exhausted);
  bool _exhausted = false;

  /// Loads the next page; returns false when there was nothing to load.
  Future<bool> loadMore() async {
    if (_loading || done) return false;
    _loading = true;
    try {
      final p = await repo.page(query, offset: _offset);
      total = p.total;
      _offset += p.items.length;
      if (p.items.isEmpty) _exhausted = true;
      for (final it in p.items) {
        if (_seen.add('${it.id}:${it.formId}')) items.add(it);
      }
      return true;
    } finally {
      _loading = false;
    }
  }

  int _offset = 0;
}
