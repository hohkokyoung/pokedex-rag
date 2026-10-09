import 'package:dio/dio.dart';

import '../api/export.dart';
import 'errors.dart';
import 'pokedex_repository.dart' show failureOf;

/// Saved teams and the builder lookups the set editor needs. Every grade, profile and
/// matchup comes from the server (ADR-009/010); this only fetches and writes.
class TeamsRepository {
  TeamsRepository(this._dio) : _api = PokeragClient(_dio);

  final Dio _dio;
  final PokeragClient _api;

  String get address => _dio.options.baseUrl;

  Future<List<TeamSummary>> teams() => _guard(() async => (await _api.listTeamsApiTeamsGet()).teams);
  Future<TeamOut> team(int id) => _guard(() => _api.getTeamApiTeamsTeamIdGet(teamId: id));
  Future<TeamOut> create(String name) => _guard(() => _api.createTeamApiTeamsPost(body: TeamCreate(name: name)));
  Future<TeamOut> rename(int id, String name) =>
      _guard(() => _api.updateTeamApiTeamsTeamIdPut(teamId: id, body: TeamUpdate(name: name)));
  Future<void> delete(int id) => _guard(() => _api.deleteTeamApiTeamsTeamIdDelete(teamId: id));

  /// Replaces a slot's whole set (the server's PUT is a full upsert, not a patch).
  Future<TeamOut> setSlot(int id, int slot, SlotUpdate set) =>
      _guard(() => _api.setSlotApiTeamsTeamIdSlotsSlotPut(teamId: id, slot: slot, body: set));
  Future<TeamOut> clearSlot(int id, int slot) => _guard(() => _api.clearSlotApiTeamsTeamIdSlotsSlotDelete(teamId: id, slot: slot));

  /// Applies a set by name; the server fills only the slot's empty parts.
  Future<TeamOut> applyBuild(int id, int slot, SlotBuild build) =>
      _guard(() => _api.applySlotBuildApiTeamsTeamIdSlotsSlotBuildPost(teamId: id, slot: slot, body: build));

  Future<TeamAnalysis> analysis(int id, {int? opponentId}) =>
      _guard(() => _api.analyzeTeamApiTeamsTeamIdAnalysisGet(teamId: id, opponentId: opponentId));
  Future<TeamStrategy> strategy(int id) => _guard(() => _api.teamStrategyProfileApiTeamsTeamIdStrategyGet(teamId: id));
  Future<TeamSummaryOut> summary(int id) => _guard(() => _api.teamSummaryTextApiTeamsTeamIdSummaryGet(teamId: id));
  Future<TeamSummaryOut> refreshSummary(int id) =>
      _guard(() => _api.teamSummaryRefreshApiTeamsTeamIdSummaryRefreshPost(teamId: id));

  // Builder lookups (legal choices only).
  Future<List<LearnsetMoveOut>> legalMoves(int pokemonId, {int? formId}) => _guard(() => formId != null
      ? _api.pokemonFormMovesApiPokemonFormsFormIdMovesGet(formId: formId)
      : _api.pokemonMovesApiPokemonPokemonIdMovesGet(pokemonId: pokemonId));
  Future<List<AbilityOut>> abilities(int pokemonId) =>
      _guard(() => _api.pokemonAbilitiesApiPokemonPokemonIdAbilitiesGet(pokemonId: pokemonId));
  Future<List<ItemOut>> heldItems(String q) => _guard(() => _api.searchItemsApiItemsGet(q: q.isEmpty ? null : q, held: true, limit: 30));
  Future<List<NatureOut>> natures() => _guard(_api.listNaturesApiNaturesGet);

  Future<T> _guard<T>(Future<T> Function() call) async {
    try {
      return await call();
    } on DioException catch (e) {
      final f = failureOf(e, address);
      // A 422 carries the server's reason (e.g. an illegal move): keep it for the user.
      if (e.response?.statusCode == 422) throw Rejected(_detail(e.response?.data));
      throw f;
    }
  }

  static String _detail(Object? body) {
    if (body is Map && body['detail'] is String) return body['detail'] as String;
    if (body is Map && body['detail'] is List) {
      return (body['detail'] as List).map((d) => d is Map ? d['msg'] : '$d').join('; ');
    }
    return 'The server rejected that change.';
  }
}
