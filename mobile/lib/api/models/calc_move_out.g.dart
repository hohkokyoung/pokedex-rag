// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'calc_move_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CalcMoveOut _$CalcMoveOutFromJson(Map<String, dynamic> json) => CalcMoveOut(
  damageClass: json['damage_class'] as String,
  name: json['name'] as String,
  power: (json['power'] as num).toInt(),
  priority: (json['priority'] as num).toInt(),
  slot: (json['slot'] as num).toInt(),
  target: json['target'] as String?,
  type: json['type'] as String,
);

Map<String, dynamic> _$CalcMoveOutToJson(CalcMoveOut instance) =>
    <String, dynamic>{
      'damage_class': instance.damageClass,
      'name': instance.name,
      'power': instance.power,
      'priority': instance.priority,
      'slot': instance.slot,
      'target': instance.target,
      'type': instance.type,
    };
