// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'offensive_profile.g.dart';

@JsonSerializable()
class OffensiveProfile {
  const OffensiveProfile({
    required this.coverageTypes,
    required this.notSuperEffective,
    required this.uncoveredTypes,
    required this.usedMoveCoverage,
    this.fromLearnset = const [],
    this.tips = const [],
  });
  
  factory OffensiveProfile.fromJson(Map<String, Object?> json) => _$OffensiveProfileFromJson(json);
  
  @JsonKey(name: 'coverage_types')
  final List<String> coverageTypes;
  @JsonKey(name: 'from_learnset')
  final List<String> fromLearnset;
  @JsonKey(name: 'not_super_effective')
  final List<String> notSuperEffective;
  final List<String> tips;
  @JsonKey(name: 'uncovered_types')
  final List<String> uncoveredTypes;
  @JsonKey(name: 'used_move_coverage')
  final bool usedMoveCoverage;

  Map<String, Object?> toJson() => _$OffensiveProfileToJson(this);
}
