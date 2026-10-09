// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'ability_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

AbilityOut _$AbilityOutFromJson(Map<String, dynamic> json) => AbilityOut(
  id: (json['id'] as num).toInt(),
  identifier: json['identifier'] as String,
  name: json['name'] as String,
  isHidden: json['is_hidden'] as bool? ?? false,
  effect: json['effect'] as String?,
  shortEffect: json['short_effect'] as String?,
);

Map<String, dynamic> _$AbilityOutToJson(AbilityOut instance) =>
    <String, dynamic>{
      'effect': instance.effect,
      'id': instance.id,
      'identifier': instance.identifier,
      'is_hidden': instance.isHidden,
      'name': instance.name,
      'short_effect': instance.shortEffect,
    };
