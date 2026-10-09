// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'strategy_axis.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

StrategyAxis _$StrategyAxisFromJson(Map<String, dynamic> json) => StrategyAxis(
  contributors: (json['contributors'] as List<dynamic>)
      .map((e) => StrategyContributor.fromJson(e as Map<String, dynamic>))
      .toList(),
  detail: json['detail'] as String,
  key: json['key'] as String,
  label: json['label'] as String,
  now: (json['now'] as num).toInt(),
  potential: (json['potential'] as num).toInt(),
  score: (json['score'] as num).toInt(),
);

Map<String, dynamic> _$StrategyAxisToJson(StrategyAxis instance) =>
    <String, dynamic>{
      'contributors': instance.contributors,
      'detail': instance.detail,
      'key': instance.key,
      'label': instance.label,
      'now': instance.now,
      'potential': instance.potential,
      'score': instance.score,
    };
