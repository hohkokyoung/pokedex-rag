// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/ability_holder_out.dart';
import '../models/ability_out.dart';
import '../models/ask_request.dart';
import '../models/ask_response.dart';
import '../models/calc_options_out.dart';
import '../models/calc_turn_out.dart';
import '../models/calc_turn_request.dart';
import '../models/catch_out.dart';
import '../models/coach_ask_request.dart';
import '../models/generation_out.dart';
import '../models/health_response.dart';
import '../models/item_out.dart';
import '../models/learnset_move_out.dart';
import '../models/move_game_learners_out.dart';
import '../models/move_out.dart';
import '../models/nature_out.dart';
import '../models/pokemon_detail.dart';
import '../models/pokemon_encounters_out.dart';
import '../models/pokemon_game_moves_out.dart';
import '../models/pokemon_list_response.dart';
import '../models/profile_out.dart';
import '../models/profile_update.dart';
import '../models/slot_build.dart';
import '../models/slot_update.dart';
import '../models/status.dart';
import '../models/team_analysis.dart';
import '../models/team_create.dart';
import '../models/team_list_response.dart';
import '../models/team_out.dart';
import '../models/team_strategy.dart';
import '../models/team_summary_out.dart';
import '../models/team_update.dart';
import '../models/type_chart_out.dart';
import '../models/type_out.dart';

part 'pokerag_client.g.dart';

@RestApi()
abstract class PokeragClient {
  factory PokeragClient(Dio dio, {String? baseUrl}) = _PokeragClient;

  /// Search Abilities.
  ///
  /// [q] - Filter abilities by name substring.
  @GET('/api/abilities')
  Future<List<AbilityOut>> searchAbilitiesApiAbilitiesGet({
    @Query('limit') int? limit = 8,
    @Query('q') String? q,
  });

  /// Ability Holders
  @GET('/api/abilities/{ability_id}/pokemon')
  Future<List<AbilityHolderOut>> abilityHoldersApiAbilitiesAbilityIdPokemonGet({
    @Path('ability_id') required int abilityId,
    @Query('limit') int? limit = 250,
  });

  /// Ask
  @POST('/api/ask')
  Future<AskResponse> askApiAskPost({
    @Body() required AskRequest body,
  });

  /// Ask Status.
  ///
  /// Whether the RAG assistant is configured, and which provider is active.
  @GET('/api/ask/status')
  Future<dynamic> askStatusApiAskStatusGet();

  /// Calc Options.
  ///
  /// The items, abilities, weather and terrain the damage maths models (static).
  @GET('/api/calc/options')
  Future<CalcOptionsOut> calcOptionsApiCalcOptionsGet();

  /// Calc Turn Route.
  ///
  /// Play one calculator turn: order, targeting, HP carried over, Focus Sash, KO calls.
  ///
  /// The same turn the website shows (``lib/calcTurn``), with types, stats and moves re-read.
  /// from the DB. Pure code, no LLM.
  @POST('/api/calc/turn')
  Future<CalcTurnOut> calcTurnRouteApiCalcTurnPost({
    @Body() required CalcTurnRequest body,
  });

  /// List Generations
  @GET('/api/generations')
  Future<List<GenerationOut>> listGenerationsApiGenerationsGet();

  /// Search Items.
  ///
  /// [q] - Filter items by name substring.
  ///
  /// [held] - Only items a Pokémon can hold in battle.
  @GET('/api/items')
  Future<List<ItemOut>> searchItemsApiItemsGet({
    @Query('limit') int? limit = 8,
    @Query('held') bool? held = false,
    @Query('q') String? q,
  });

  /// Search Moves.
  ///
  /// [q] - Filter moves by name substring.
  @GET('/api/moves')
  Future<List<MoveOut>> searchMovesApiMovesGet({
    @Query('limit') int? limit = 8,
    @Query('q') String? q,
  });

  /// Move Learners By Game.
  ///
  /// [versionGroup] - Game id; omit for every game.
  @GET('/api/moves/{move_id}/learners/by-game')
  Future<MoveGameLearnersOut> moveLearnersByGameApiMovesMoveIdLearnersByGameGet({
    @Path('move_id') required int moveId,
    @Query('version_group') int? versionGroup,
  });

  /// List Natures
  @GET('/api/natures')
  Future<List<NatureOut>> listNaturesApiNaturesGet();

  /// List Pokemon.
  ///
  /// [q] - Search by name or dex number.
  ///
  /// [type] - Filter by type id(s); all must match.
  ///
  /// [generation] - Filter by generation(s) 1-9; any may match.
  @GET('/api/pokemon')
  Future<PokemonListResponse> listPokemonApiPokemonGet({
    @Query('sort') String? sort = 'dex',
    @Query('order') String? order = 'asc',
    @Query('limit') int? limit = 40,
    @Query('offset') int? offset = 0,
    @Query('q') String? q,
    @Query('type') List<String>? type,
    @Query('generation') List<int>? generation,
    @Query('legendary') bool? legendary,
    @Query('mythical') bool? mythical,
  });

  /// Pokemon Form Moves.
  ///
  /// [q] - Filter moves by name substring.
  @GET('/api/pokemon/forms/{form_id}/moves')
  Future<List<LearnsetMoveOut>> pokemonFormMovesApiPokemonFormsFormIdMovesGet({
    @Path('form_id') required int formId,
    @Query('q') String? q,
  });

  /// Get Pokemon
  @GET('/api/pokemon/{id_or_name}')
  Future<PokemonDetail> getPokemonApiPokemonIdOrNameGet({
    @Path('id_or_name') required String idOrName,
  });

  /// Pokemon Abilities
  @GET('/api/pokemon/{pokemon_id}/abilities')
  Future<List<AbilityOut>> pokemonAbilitiesApiPokemonPokemonIdAbilitiesGet({
    @Path('pokemon_id') required int pokemonId,
  });

  /// Catch Odds.
  ///
  /// Every ball ranked by catch chance for this situation (Gen 8+ formula).
  ///
  /// [level] - Wild level.
  ///
  /// [myLevel] - Your lead's level (Level Ball).
  ///
  /// [hpPct] - Wild HP left, %.
  ///
  /// [night] - Night or in a cave (Dusk Ball).
  ///
  /// [water] - Fishing, surfing or underwater (Dive, Lure).
  ///
  /// [caught] - Species caught before (Repeat Ball).
  ///
  /// [loveMatch] - Lead: same species, opposite gender.
  ///
  /// [dexCaught] - Species caught (critical capture).
  ///
  /// [charm] - Catching Charm.
  @GET('/api/pokemon/{pokemon_id}/catch')
  Future<CatchOut> catchOddsApiPokemonPokemonIdCatchGet({
    @Path('pokemon_id') required int pokemonId,
    @Query('level') int? level = 30,
    @Query('my_level') int? myLevel = 30,
    @Query('hp_pct') int? hpPct = 100,
    @Query('turn') int? turn = 1,
    @Query('status') Status? status = Status.none,
    @Query('night') bool? night = false,
    @Query('water') bool? water = false,
    @Query('caught') bool? caught = false,
    @Query('love_match') bool? loveMatch = false,
    @Query('dex_caught') int? dexCaught = 0,
    @Query('charm') bool? charm = false,
  });

  /// Pokemon Encounters.
  ///
  /// Where a species or form (id > 10000) is found in the wild, one game at a time.
  ///
  /// [version] - Game (version) id; omit for the newest.
  @GET('/api/pokemon/{pokemon_id}/encounters')
  Future<PokemonEncountersOut> pokemonEncountersApiPokemonPokemonIdEncountersGet({
    @Path('pokemon_id') required int pokemonId,
    @Query('version') int? version,
  });

  /// Pokemon Moves.
  ///
  /// [q] - Filter moves by name substring.
  @GET('/api/pokemon/{pokemon_id}/moves')
  Future<List<LearnsetMoveOut>> pokemonMovesApiPokemonPokemonIdMovesGet({
    @Path('pokemon_id') required int pokemonId,
    @Query('q') String? q,
  });

  /// Pokemon Moves By Game.
  ///
  /// A species' or form's (id > 10000) learnset in one game, with TM labels.
  ///
  /// [versionGroup] - Game id; omit for the newest game.
  @GET('/api/pokemon/{pokemon_id}/moves/by-game')
  Future<PokemonGameMovesOut> pokemonMovesByGameApiPokemonPokemonIdMovesByGameGet({
    @Path('pokemon_id') required int pokemonId,
    @Query('version_group') int? versionGroup,
  });

  /// Get Profile
  @GET('/api/profile')
  Future<ProfileOut> getProfileApiProfileGet();

  /// Update Profile
  @PUT('/api/profile')
  Future<ProfileOut> updateProfileApiProfilePut({
    @Body() required ProfileUpdate body,
  });

  /// Remove Favorite
  @DELETE('/api/profile/favorites/{pokemon_id}')
  Future<ProfileOut> removeFavoriteApiProfileFavoritesPokemonIdDelete({
    @Path('pokemon_id') required int pokemonId,
  });

  /// Add Favorite
  @POST('/api/profile/favorites/{pokemon_id}')
  Future<ProfileOut> addFavoriteApiProfileFavoritesPokemonIdPost({
    @Path('pokemon_id') required int pokemonId,
  });

  /// List Teams
  @GET('/api/teams')
  Future<TeamListResponse> listTeamsApiTeamsGet({
    @Query('kind') String? kind,
  });

  /// Create Team
  @POST('/api/teams')
  Future<TeamOut> createTeamApiTeamsPost({
    @Body() required TeamCreate body,
  });

  /// Delete Team
  @DELETE('/api/teams/{team_id}')
  Future<void> deleteTeamApiTeamsTeamIdDelete({
    @Path('team_id') required int teamId,
  });

  /// Get Team
  @GET('/api/teams/{team_id}')
  Future<TeamOut> getTeamApiTeamsTeamIdGet({
    @Path('team_id') required int teamId,
  });

  /// Update Team
  @PUT('/api/teams/{team_id}')
  Future<TeamOut> updateTeamApiTeamsTeamIdPut({
    @Path('team_id') required int teamId,
    @Body() required TeamUpdate body,
  });

  /// Analyze Team.
  ///
  /// [opponentId] - Compare against a saved opponent team.
  @GET('/api/teams/{team_id}/analysis')
  Future<TeamAnalysis> analyzeTeamApiTeamsTeamIdAnalysisGet({
    @Path('team_id') required int teamId,
    @Query('opponent_id') int? opponentId,
  });

  /// Coach Ask.
  ///
  /// SSE coaching over a team, planned like Ask (see ``app.agent``).
  ///
  /// Events: ``plan`` (the team context step first), ``step``*, ``view``* (candidates,.
  /// set-edit proposals, adds, duels and dex views), ``team_updated`` after an explicit.
  /// add, ``sources``, ``delta``*, ``done``.
  @POST('/api/teams/{team_id}/ask')
  Future<void> coachAskApiTeamsTeamIdAskPost({
    @Path('team_id') required int teamId,
    @Body() required CoachAskRequest body,
  });

  /// Clear Slot
  @DELETE('/api/teams/{team_id}/slots/{slot}')
  Future<TeamOut> clearSlotApiTeamsTeamIdSlotsSlotDelete({
    @Path('team_id') required int teamId,
    @Path('slot') required int slot,
  });

  /// Set Slot
  @PUT('/api/teams/{team_id}/slots/{slot}')
  Future<TeamOut> setSlotApiTeamsTeamIdSlotsSlotPut({
    @Path('team_id') required int teamId,
    @Path('slot') required int slot,
    @Body() required SlotUpdate body,
  });

  /// Apply Slot Build.
  ///
  /// Apply a set given by name (the coach's or the engine's suggestion) to a slot.
  @POST('/api/teams/{team_id}/slots/{slot}/build')
  Future<TeamOut> applySlotBuildApiTeamsTeamIdSlotsSlotBuildPost({
    @Path('team_id') required int teamId,
    @Path('slot') required int slot,
    @Body() required SlotBuild body,
  });

  /// Team Strategy Profile.
  ///
  /// How the team wants to win: offense/bulk/speed/setup/stall/support, each traceable.
  @GET('/api/teams/{team_id}/strategy')
  Future<TeamStrategy> teamStrategyProfileApiTeamsTeamIdStrategyGet({
    @Path('team_id') required int teamId,
  });

  /// Team Summary Text.
  ///
  /// Stored summary; never waits on the LLM. ``pending`` = a rewrite is underway.
  @GET('/api/teams/{team_id}/summary')
  Future<TeamSummaryOut> teamSummaryTextApiTeamsTeamIdSummaryGet({
    @Path('team_id') required int teamId,
  });

  /// Team Summary Refresh.
  ///
  /// Force a fresh summary now (the detail page's Regenerate button).
  @POST('/api/teams/{team_id}/summary/refresh')
  Future<TeamSummaryOut> teamSummaryRefreshApiTeamsTeamIdSummaryRefreshPost({
    @Path('team_id') required int teamId,
  });

  /// List Types
  @GET('/api/types')
  Future<List<TypeOut>> listTypesApiTypesGet();

  /// Type Chart.
  ///
  /// The type-effectiveness chart, from the ingested data. Static: clients fetch it once.
  @GET('/api/types/chart')
  Future<TypeChartOut> typeChartApiTypesChartGet();

  /// Health.
  ///
  /// Liveness probe — the process is running.
  @GET('/health')
  Future<HealthResponse> healthHealthGet();
}
