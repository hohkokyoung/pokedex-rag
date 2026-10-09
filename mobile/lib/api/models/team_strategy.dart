// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'strategy_axis.dart';

part 'team_strategy.g.dart';

@JsonSerializable()
class TeamStrategy {
  const TeamStrategy({
    required this.axes,
    required this.style,
    required this.styleReason,
    required this.teamId,
  });
  
  factory TeamStrategy.fromJson(Map<String, Object?> json) => _$TeamStrategyFromJson(json);
  
  final List<StrategyAxis> axes;
  final String style;
  @JsonKey(name: 'style_reason')
  final String styleReason;
  @JsonKey(name: 'team_id')
  final int teamId;

  Map<String, Object?> toJson() => _$TeamStrategyToJson(this);
}
