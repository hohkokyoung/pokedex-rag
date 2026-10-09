// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pokemon_encounters_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PokemonEncountersOut _$PokemonEncountersOutFromJson(
  Map<String, dynamic> json,
) => PokemonEncountersOut(
  encounters: (json['encounters'] as List<dynamic>)
      .map((e) => EncounterOut.fromJson(e as Map<String, dynamic>))
      .toList(),
  games: (json['games'] as List<dynamic>)
      .map((e) => EncounterGameOut.fromJson(e as Map<String, dynamic>))
      .toList(),
  versionId: (json['version_id'] as num?)?.toInt(),
);

Map<String, dynamic> _$PokemonEncountersOutToJson(
  PokemonEncountersOut instance,
) => <String, dynamic>{
  'encounters': instance.encounters,
  'games': instance.games,
  'version_id': instance.versionId,
};
