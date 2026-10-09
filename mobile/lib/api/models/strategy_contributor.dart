// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'strategy_contributor.g.dart';

@JsonSerializable()
class StrategyContributor {
  const StrategyContributor({
    required this.moves,
    required this.name,
    required this.setValue,
  });
  
  factory StrategyContributor.fromJson(Map<String, Object?> json) => _$StrategyContributorFromJson(json);
  
  final List<String> moves;
  final String name;

  /// The name has been replaced because it contains a keyword. Original name: `set`.
  @JsonKey(name: 'set')
  final bool setValue;

  Map<String, Object?> toJson() => _$StrategyContributorToJson(this);
}
