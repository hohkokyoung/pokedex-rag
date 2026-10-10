// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'calc_hit_in.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CalcHitIn _$CalcHitInFromJson(Map<String, dynamic> json) => CalcHitIn(
  attacker: (json['attacker'] as num).toInt(),
  maxPct: json['max_pct'] as num,
  minPct: json['min_pct'] as num,
  move: json['move'] as String,
  target: (json['target'] as num).toInt(),
  ko: (json['ko'] as num?)?.toInt() ?? 0,
  te: json['te'] as num? ?? 1,
);

Map<String, dynamic> _$CalcHitInToJson(CalcHitIn instance) => <String, dynamic>{
  'attacker': instance.attacker,
  'ko': instance.ko,
  'max_pct': instance.maxPct,
  'min_pct': instance.minPct,
  'move': instance.move,
  'target': instance.target,
  'te': instance.te,
};
