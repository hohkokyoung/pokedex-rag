// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'vs_member.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

VsMember _$VsMemberFromJson(Map<String, dynamic> json) => VsMember(
  bst: (json['bst'] as num).toInt(),
  name: json['name'] as String,
  pokemonId: (json['pokemon_id'] as num).toInt(),
  role: json['role'] as String,
  slot: (json['slot'] as num).toInt(),
  speed: (json['speed'] as num).toInt(),
  spriteUrl: json['sprite_url'] as String,
  types: (json['types'] as List<dynamic>).map((e) => e as String).toList(),
);

Map<String, dynamic> _$VsMemberToJson(VsMember instance) => <String, dynamic>{
  'bst': instance.bst,
  'name': instance.name,
  'pokemon_id': instance.pokemonId,
  'role': instance.role,
  'slot': instance.slot,
  'speed': instance.speed,
  'sprite_url': instance.spriteUrl,
  'types': instance.types,
};
