// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'damage_view.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

DamageView _$DamageViewFromJson(Map<String, dynamic> json) => DamageView(
  attacker: CalcRef.fromJson(json['attacker'] as Map<String, dynamic>),
  current: HitRange.fromJson(json['current'] as Map<String, dynamic>),
  defender: CalcRef.fromJson(json['defender'] as Map<String, dynamic>),
  move: MoveRow.fromJson(json['move'] as Map<String, dynamic>),
  kind: json['kind'] as String? ?? 'damage',
  apply: (json['apply'] as List<dynamic>?)
      ?.map((e) => CalcApply.fromJson(e as Map<String, dynamic>))
      .toList(),
  changes: json['changes'] as List<dynamic>?,
  chunkRefs: (json['chunk_refs'] as List<dynamic>?)
      ?.map((e) => (e as num).toInt())
      .toList(),
  step: json['step'] as String?,
  whatif: json['whatif'] == null
      ? null
      : HitRange.fromJson(json['whatif'] as Map<String, dynamic>),
);

Map<String, dynamic> _$DamageViewToJson(DamageView instance) =>
    <String, dynamic>{
      'apply': instance.apply,
      'attacker': instance.attacker,
      'changes': instance.changes,
      'chunk_refs': instance.chunkRefs,
      'current': instance.current,
      'defender': instance.defender,
      'kind': instance.kind,
      'move': instance.move,
      'step': instance.step,
      'whatif': instance.whatif,
    };
