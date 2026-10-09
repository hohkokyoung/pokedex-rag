// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'member_role.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MemberRole _$MemberRoleFromJson(Map<String, dynamic> json) => MemberRole(
  bst: (json['bst'] as num).toInt(),
  bulk: (json['bulk'] as num).toInt(),
  name: json['name'] as String,
  offense: (json['offense'] as num).toInt(),
  role: json['role'] as String,
  slot: (json['slot'] as num).toInt(),
  speed: (json['speed'] as num).toInt(),
  effSpeed: (json['eff_speed'] as num?)?.toInt(),
  speedNote: json['speed_note'] as String?,
);

Map<String, dynamic> _$MemberRoleToJson(MemberRole instance) =>
    <String, dynamic>{
      'bst': instance.bst,
      'bulk': instance.bulk,
      'eff_speed': instance.effSpeed,
      'name': instance.name,
      'offense': instance.offense,
      'role': instance.role,
      'slot': instance.slot,
      'speed': instance.speed,
      'speed_note': instance.speedNote,
    };
