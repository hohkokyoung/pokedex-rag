// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'verdict.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

Verdict _$VerdictFromJson(Map<String, dynamic> json) => Verdict(
  edge: VerdictEdge.fromJson(json['edge'] as String),
  label: json['label'] as String,
  reason: json['reason'] as String,
  score: (json['score'] as num).toInt(),
);

Map<String, dynamic> _$VerdictToJson(Verdict instance) => <String, dynamic>{
  'edge': _$VerdictEdgeEnumMap[instance.edge]!,
  'label': instance.label,
  'reason': instance.reason,
  'score': instance.score,
};

const _$VerdictEdgeEnumMap = {
  VerdictEdge.ours: 'ours',
  VerdictEdge.theirs: 'theirs',
  VerdictEdge.even: 'even',
  VerdictEdge.$unknown: r'$unknown',
};
