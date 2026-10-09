// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'survive_view.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SurviveView _$SurviveViewFromJson(Map<String, dynamic> json) => SurviveView(
  attacker: CalcRef.fromJson(json['attacker'] as Map<String, dynamic>),
  current: HitRange.fromJson(json['current'] as Map<String, dynamic>),
  defender: CalcRef.fromJson(json['defender'] as Map<String, dynamic>),
  hpEv: (json['hp_ev'] as num).toInt(),
  move: MoveRow.fromJson(json['move'] as Map<String, dynamic>),
  nature: json['nature'] as String,
  natureChanged: json['nature_changed'] as bool,
  range: HitRange.fromJson(json['range'] as Map<String, dynamic>),
  stat: SurviveViewStat.fromJson(json['stat'] as String),
  statEv: (json['stat_ev'] as num).toInt(),
  survives: json['survives'] as bool,
  apply: json['apply'] == null
      ? null
      : CalcApply.fromJson(json['apply'] as Map<String, dynamic>),
  chunkRefs: (json['chunk_refs'] as List<dynamic>?)
      ?.map((e) => (e as num).toInt())
      .toList(),
  step: json['step'] as String?,
  already: json['already'] as bool? ?? false,
  kind: json['kind'] as String? ?? 'survive',
);

Map<String, dynamic> _$SurviveViewToJson(SurviveView instance) =>
    <String, dynamic>{
      'already': instance.already,
      'apply': instance.apply,
      'attacker': instance.attacker,
      'chunk_refs': instance.chunkRefs,
      'current': instance.current,
      'defender': instance.defender,
      'hp_ev': instance.hpEv,
      'kind': instance.kind,
      'move': instance.move,
      'nature': instance.nature,
      'nature_changed': instance.natureChanged,
      'range': instance.range,
      'stat': _$SurviveViewStatEnumMap[instance.stat]!,
      'stat_ev': instance.statEv,
      'step': instance.step,
      'survives': instance.survives,
    };

const _$SurviveViewStatEnumMap = {
  SurviveViewStat.def: 'def',
  SurviveViewStat.spd: 'spd',
  SurviveViewStat.$unknown: r'$unknown',
};
