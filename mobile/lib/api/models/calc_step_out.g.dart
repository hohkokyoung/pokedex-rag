// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'calc_step_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CalcStepOut _$CalcStepOutFromJson(Map<String, dynamic> json) => CalcStepOut(
  atRisk: json['at_risk'] as bool,
  hits: (json['hits'] as List<dynamic>)
      .map((e) => CalcHitOut.fromJson(e as Map<String, dynamic>))
      .toList(),
  skipped: json['skipped'] as bool,
  slot: (json['slot'] as num).toInt(),
);

Map<String, dynamic> _$CalcStepOutToJson(CalcStepOut instance) =>
    <String, dynamic>{
      'at_risk': instance.atRisk,
      'hits': instance.hits,
      'skipped': instance.skipped,
      'slot': instance.slot,
    };
