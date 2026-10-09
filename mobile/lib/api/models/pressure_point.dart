// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'pressure_point.g.dart';

/// One of *our* members and the opponents it hits super-effectively.
@JsonSerializable()
class PressurePoint {
  const PressurePoint({
    required this.attacker,
    required this.attackerTypes,
    required this.targets,
    required this.via,
  });
  
  factory PressurePoint.fromJson(Map<String, Object?> json) => _$PressurePointFromJson(json);
  
  final String attacker;
  @JsonKey(name: 'attacker_types')
  final List<String> attackerTypes;
  final List<String> targets;
  final List<String> via;

  Map<String, Object?> toJson() => _$PressurePointToJson(this);
}
