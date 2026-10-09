// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'score_row_edge.dart';

part 'score_row.g.dart';

@JsonSerializable()
class ScoreRow {
  const ScoreRow({
    required this.edge,
    required this.key,
    required this.label,
    required this.ours,
    required this.oursLabel,
    required this.share,
    required this.theirs,
    required this.theirsLabel,
    required this.weight,
  });
  
  factory ScoreRow.fromJson(Map<String, Object?> json) => _$ScoreRowFromJson(json);
  
  final ScoreRowEdge edge;
  final String key;
  final String label;
  final num ours;
  @JsonKey(name: 'ours_label')
  final String oursLabel;
  final num share;
  final num theirs;
  @JsonKey(name: 'theirs_label')
  final String theirsLabel;
  final num weight;

  Map<String, Object?> toJson() => _$ScoreRowToJson(this);
}
