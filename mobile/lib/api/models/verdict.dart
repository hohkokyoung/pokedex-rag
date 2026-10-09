// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'verdict_edge.dart';

part 'verdict.g.dart';

@JsonSerializable()
class Verdict {
  const Verdict({
    required this.edge,
    required this.label,
    required this.reason,
    required this.score,
  });
  
  factory Verdict.fromJson(Map<String, Object?> json) => _$VerdictFromJson(json);
  
  final VerdictEdge edge;
  final String label;
  final String reason;
  final int score;

  Map<String, Object?> toJson() => _$VerdictToJson(this);
}
