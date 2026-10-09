// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'encounter_game_out.dart';
import 'encounter_out.dart';

part 'pokemon_encounters_out.g.dart';

/// Where a Pokémon is found in one game, plus every game it can be found in.
@JsonSerializable()
class PokemonEncountersOut {
  const PokemonEncountersOut({
    required this.encounters,
    required this.games,
    required this.versionId,
  });
  
  factory PokemonEncountersOut.fromJson(Map<String, Object?> json) => _$PokemonEncountersOutFromJson(json);
  
  final List<EncounterOut> encounters;
  final List<EncounterGameOut> games;
  @JsonKey(name: 'version_id')
  final int? versionId;

  Map<String, Object?> toJson() => _$PokemonEncountersOutToJson(this);
}
