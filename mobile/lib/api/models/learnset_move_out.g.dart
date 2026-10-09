// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'learnset_move_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

LearnsetMoveOut _$LearnsetMoveOutFromJson(Map<String, dynamic> json) =>
    LearnsetMoveOut(
      identifier: json['identifier'] as String,
      moveId: (json['move_id'] as num).toInt(),
      name: json['name'] as String,
      priority: (json['priority'] as num?)?.toInt() ?? 0,
      accuracy: (json['accuracy'] as num?)?.toInt(),
      damageClass: json['damage_class'] as String?,
      learnMethod: json['learn_method'] as String?,
      level: (json['level'] as num?)?.toInt(),
      power: (json['power'] as num?)?.toInt(),
      pp: (json['pp'] as num?)?.toInt(),
      shortEffect: json['short_effect'] as String?,
      target: json['target'] as String?,
      type: json['type'] as String?,
    );

Map<String, dynamic> _$LearnsetMoveOutToJson(LearnsetMoveOut instance) =>
    <String, dynamic>{
      'accuracy': instance.accuracy,
      'damage_class': instance.damageClass,
      'identifier': instance.identifier,
      'learn_method': instance.learnMethod,
      'level': instance.level,
      'move_id': instance.moveId,
      'name': instance.name,
      'power': instance.power,
      'pp': instance.pp,
      'priority': instance.priority,
      'short_effect': instance.shortEffect,
      'target': instance.target,
      'type': instance.type,
    };
