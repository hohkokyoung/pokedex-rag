// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'calc_hit_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CalcHitOut _$CalcHitOutFromJson(Map<String, dynamic> json) => CalcHitOut(
  attack: (json['attack'] as num).toInt(),
  attacker: (json['attacker'] as num).toInt(),
  baseValue: (json['base'] as num).toInt(),
  defense: (json['defense'] as num).toInt(),
  friendlyFire: json['friendly_fire'] as bool,
  ko: json['ko'] == null ? null : CalcHitOutKo.fromJson(json['ko'] as String),
  koHits: (json['ko_hits'] as num).toInt(),
  maxPct: json['max_pct'] as num,
  minPct: json['min_pct'] as num,
  mod: json['mod'] as num,
  move: json['move'] as String,
  sash: json['sash'] as bool,
  stab: json['stab'] as num,
  target: (json['target'] as num).toInt(),
  te: json['te'] as num,
);

Map<String, dynamic> _$CalcHitOutToJson(CalcHitOut instance) =>
    <String, dynamic>{
      'attack': instance.attack,
      'attacker': instance.attacker,
      'base': instance.baseValue,
      'defense': instance.defense,
      'friendly_fire': instance.friendlyFire,
      'ko': _$CalcHitOutKoEnumMap[instance.ko],
      'ko_hits': instance.koHits,
      'max_pct': instance.maxPct,
      'min_pct': instance.minPct,
      'mod': instance.mod,
      'move': instance.move,
      'sash': instance.sash,
      'stab': instance.stab,
      'target': instance.target,
      'te': instance.te,
    };

const _$CalcHitOutKoEnumMap = {
  CalcHitOutKo.yes: 'yes',
  CalcHitOutKo.maybe: 'maybe',
  CalcHitOutKo.$unknown: r'$unknown',
};
