// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'move_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MoveOut _$MoveOutFromJson(Map<String, dynamic> json) => MoveOut(
  id: (json['id'] as num).toInt(),
  identifier: json['identifier'] as String,
  name: json['name'] as String,
  priority: (json['priority'] as num?)?.toInt() ?? 0,
  accuracy: (json['accuracy'] as num?)?.toInt(),
  damageClass: json['damage_class'] as String?,
  power: (json['power'] as num?)?.toInt(),
  pp: (json['pp'] as num?)?.toInt(),
  shortEffect: json['short_effect'] as String?,
  signatureZ: json['signature_z'] == null
      ? null
      : SignatureZOut.fromJson(json['signature_z'] as Map<String, dynamic>),
  type: json['type'] as String?,
);

Map<String, dynamic> _$MoveOutToJson(MoveOut instance) => <String, dynamic>{
  'accuracy': instance.accuracy,
  'damage_class': instance.damageClass,
  'id': instance.id,
  'identifier': instance.identifier,
  'name': instance.name,
  'power': instance.power,
  'pp': instance.pp,
  'priority': instance.priority,
  'short_effect': instance.shortEffect,
  'signature_z': instance.signatureZ,
  'type': instance.type,
};
