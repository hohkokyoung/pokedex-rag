// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'stats_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

StatsOut _$StatsOutFromJson(Map<String, dynamic> json) => StatsOut(
  attack: (json['attack'] as num).toInt(),
  defense: (json['defense'] as num).toInt(),
  hp: (json['hp'] as num).toInt(),
  spAttack: (json['sp_attack'] as num).toInt(),
  spDefense: (json['sp_defense'] as num).toInt(),
  speed: (json['speed'] as num).toInt(),
  total: (json['total'] as num).toInt(),
);

Map<String, dynamic> _$StatsOutToJson(StatsOut instance) => <String, dynamic>{
  'attack': instance.attack,
  'defense': instance.defense,
  'hp': instance.hp,
  'sp_attack': instance.spAttack,
  'sp_defense': instance.spDefense,
  'speed': instance.speed,
  'total': instance.total,
};
