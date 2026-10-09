// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'move_row.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MoveRow _$MoveRowFromJson(Map<String, dynamic> json) => MoveRow(
  name: json['name'] as String,
  type: json['type'] as String,
  accuracy: (json['accuracy'] as num?)?.toInt(),
  damageClass: json['damage_class'] as String?,
  effect: json['effect'] as String?,
  learners: (json['learners'] as num?)?.toInt(),
  moveId: (json['move_id'] as num?)?.toInt(),
  power: (json['power'] as num?)?.toInt(),
  pp: (json['pp'] as num?)?.toInt(),
  ref: (json['ref'] as num?)?.toInt(),
);

Map<String, dynamic> _$MoveRowToJson(MoveRow instance) => <String, dynamic>{
  'accuracy': instance.accuracy,
  'damage_class': instance.damageClass,
  'effect': instance.effect,
  'learners': instance.learners,
  'move_id': instance.moveId,
  'name': instance.name,
  'power': instance.power,
  'pp': instance.pp,
  'ref': instance.ref,
  'type': instance.type,
};
