// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'strategy_contributor.dart';

part 'strategy_axis.g.dart';

@JsonSerializable()
class StrategyAxis {
  const StrategyAxis({
    required this.contributors,
    required this.detail,
    required this.key,
    required this.label,
    required this.now,
    required this.potential,
    required this.score,
  });
  
  factory StrategyAxis.fromJson(Map<String, Object?> json) => _$StrategyAxisFromJson(json);
  
  final List<StrategyContributor> contributors;
  final String detail;
  final String key;
  final String label;
  final int now;
  final int potential;
  final int score;

  Map<String, Object?> toJson() => _$StrategyAxisToJson(this);
}
