// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/generation_out.dart';
import '../models/health_response.dart';
import '../models/pokemon_detail.dart';
import '../models/pokemon_list_response.dart';
import '../models/type_chart_out.dart';
import '../models/type_out.dart';

part 'pokerag_client.g.dart';

@RestApi()
abstract class PokeragClient {
  factory PokeragClient(Dio dio, {String? baseUrl}) = _PokeragClient;

  /// List Generations
  @GET('/api/generations')
  Future<List<GenerationOut>> listGenerationsApiGenerationsGet();

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
