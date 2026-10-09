// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'suggested_move.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SuggestedMove _$SuggestedMoveFromJson(Map<String, dynamic> json) =>
    SuggestedMove(
      isSet: json['is_set'] as bool,
      name: json['name'] as String,
      damageClass: json['damage_class'] as String?,
      power: (json['power'] as num?)?.toInt(),
      type: json['type'] as String?,
    );

Map<String, dynamic> _$SuggestedMoveToJson(SuggestedMove instance) =>
    <String, dynamic>{
      'damage_class': instance.damageClass,
      'is_set': instance.isSet,
      'name': instance.name,
      'power': instance.power,
      'type': instance.type,
    };
