// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'encounter_game_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

EncounterGameOut _$EncounterGameOutFromJson(Map<String, dynamic> json) =>
    EncounterGameOut(
      generation: (json['generation'] as num).toInt(),
      places: (json['places'] as num).toInt(),
      version: json['version'] as String,
      versionId: (json['version_id'] as num).toInt(),
    );

Map<String, dynamic> _$EncounterGameOutToJson(EncounterGameOut instance) =>
    <String, dynamic>{
      'generation': instance.generation,
      'places': instance.places,
      'version': instance.version,
      'version_id': instance.versionId,
    };
