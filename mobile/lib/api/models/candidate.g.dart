// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'candidate.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

Candidate _$CandidateFromJson(Map<String, dynamic> json) => Candidate(
  baseStats: Map<String, int>.from(json['base_stats'] as Map),
  dexNumber: (json['dex_number'] as num).toInt(),
  name: json['name'] as String,
  pokemonId: (json['pokemon_id'] as num).toInt(),
  reason: json['reason'] as String,
  role: json['role'] as String,
  spriteUrl: json['sprite_url'] as String,
  types: (json['types'] as List<dynamic>).map((e) => e as String).toList(),
);

Map<String, dynamic> _$CandidateToJson(Candidate instance) => <String, dynamic>{
  'base_stats': instance.baseStats,
  'dex_number': instance.dexNumber,
  'name': instance.name,
  'pokemon_id': instance.pokemonId,
  'reason': instance.reason,
  'role': instance.role,
  'sprite_url': instance.spriteUrl,
  'types': instance.types,
};
