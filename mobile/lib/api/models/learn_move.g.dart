// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'learn_move.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

LearnMove _$LearnMoveFromJson(Map<String, dynamic> json) => LearnMove(
  name: json['name'] as String,
  type: json['type'] as String,
  damageClass: json['damage_class'] as String?,
  level: (json['level'] as num?)?.toInt(),
  levelNote: json['level_note'] as String?,
  power: (json['power'] as num?)?.toInt(),
);

Map<String, dynamic> _$LearnMoveToJson(LearnMove instance) => <String, dynamic>{
  'damage_class': instance.damageClass,
  'level': instance.level,
  'level_note': instance.levelNote,
  'name': instance.name,
  'power': instance.power,
  'type': instance.type,
};
