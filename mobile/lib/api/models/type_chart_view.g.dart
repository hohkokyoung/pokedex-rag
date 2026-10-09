// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'type_chart_view.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TypeChartView _$TypeChartViewFromJson(
  Map<String, dynamic> json,
) => TypeChartView(
  types: (json['types'] as List<dynamic>).map((e) => e as String).toList(),
  kind: json['kind'] as String? ?? 'type_chart',
  chunkRefs: (json['chunk_refs'] as List<dynamic>?)
      ?.map((e) => (e as num).toInt())
      .toList(),
  immune: (json['immune'] as List<dynamic>?)?.map((e) => e as String).toList(),
  resistHalf: (json['resist_half'] as List<dynamic>?)
      ?.map((e) => e as String)
      .toList(),
  resistQuarter: (json['resist_quarter'] as List<dynamic>?)
      ?.map((e) => e as String)
      .toList(),
  step: json['step'] as String?,
  strongAgainst: (json['strong_against'] as List<dynamic>?)
      ?.map((e) => e as String)
      .toList(),
  weak2x: (json['weak_2x'] as List<dynamic>?)?.map((e) => e as String).toList(),
  weak4x: (json['weak_4x'] as List<dynamic>?)?.map((e) => e as String).toList(),
);

Map<String, dynamic> _$TypeChartViewToJson(TypeChartView instance) =>
    <String, dynamic>{
      'chunk_refs': instance.chunkRefs,
      'immune': instance.immune,
      'kind': instance.kind,
      'resist_half': instance.resistHalf,
      'resist_quarter': instance.resistQuarter,
      'step': instance.step,
      'strong_against': instance.strongAgainst,
      'types': instance.types,
      'weak_2x': instance.weak2x,
      'weak_4x': instance.weak4x,
    };
