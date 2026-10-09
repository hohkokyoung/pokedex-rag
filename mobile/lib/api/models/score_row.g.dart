// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'score_row.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ScoreRow _$ScoreRowFromJson(Map<String, dynamic> json) => ScoreRow(
  edge: ScoreRowEdge.fromJson(json['edge'] as String),
  key: json['key'] as String,
  label: json['label'] as String,
  ours: json['ours'] as num,
  oursLabel: json['ours_label'] as String,
  share: json['share'] as num,
  theirs: json['theirs'] as num,
  theirsLabel: json['theirs_label'] as String,
  weight: json['weight'] as num,
);

Map<String, dynamic> _$ScoreRowToJson(ScoreRow instance) => <String, dynamic>{
  'edge': _$ScoreRowEdgeEnumMap[instance.edge]!,
  'key': instance.key,
  'label': instance.label,
  'ours': instance.ours,
  'ours_label': instance.oursLabel,
  'share': instance.share,
  'theirs': instance.theirs,
  'theirs_label': instance.theirsLabel,
  'weight': instance.weight,
};

const _$ScoreRowEdgeEnumMap = {
  ScoreRowEdge.ours: 'ours',
  ScoreRowEdge.theirs: 'theirs',
  ScoreRowEdge.even: 'even',
  ScoreRowEdge.$unknown: r'$unknown',
};
