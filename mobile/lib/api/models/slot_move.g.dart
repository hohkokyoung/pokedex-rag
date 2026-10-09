// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'slot_move.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SlotMove _$SlotMoveFromJson(Map<String, dynamic> json) => SlotMove(
  moveId: (json['move_id'] as num).toInt(),
  name: json['name'] as String,
  priority: (json['priority'] as num?)?.toInt() ?? 0,
  accuracy: (json['accuracy'] as num?)?.toInt(),
  damageClass: json['damage_class'] as String?,
  power: (json['power'] as num?)?.toInt(),
  type: json['type'] as String?,
);

Map<String, dynamic> _$SlotMoveToJson(SlotMove instance) => <String, dynamic>{
  'accuracy': instance.accuracy,
  'damage_class': instance.damageClass,
  'move_id': instance.moveId,
  'name': instance.name,
  'power': instance.power,
  'priority': instance.priority,
  'type': instance.type,
};
