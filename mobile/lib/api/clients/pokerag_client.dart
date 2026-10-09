// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/generation_out.dart';
import '../models/health_response.dart';
import '../models/move_game_learners_out.dart';
import '../models/pokemon_detail.dart';
import '../models/pokemon_encounters_out.dart';
import '../models/pokemon_game_moves_out.dart';
import '../models/pokemon_list_response.dart';
import '../models/profile_out.dart';
import '../models/profile_update.dart';
import '../models/type_chart_out.dart';
import '../models/type_out.dart';

part 'pokerag_client.g.dart';

@RestApi()
abstract class PokeragClient {
  factory PokeragClient(Dio dio, {String? baseUrl}) = _PokeragClient;

  /// List Generations
  @GET('/api/generations')
  Future<List<GenerationOut>> listGenerationsApiGenerationsGet();

  /// Move Learners By Game.
  ///
  /// [versionGroup] - Game id; omit for every game.
  @GET('/api/moves/{move_id}/learners/by-game')
  Future<MoveGameLearnersOut> moveLearnersByGameApiMovesMoveIdLearnersByGameGet({
    @Path('move_id') required int moveId,
    @Query('version_group') int? versionGroup,
  });

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

  /// Get Pokemon
  @GET('/api/pokemon/{id_or_name}')
  Future<PokemonDetail> getPokemonApiPokemonIdOrNameGet({
    @Path('id_or_name') required String idOrName,
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
