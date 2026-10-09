// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'encounter_out.g.dart';

@JsonSerializable()
class EncounterOut {
  const EncounterOut({
    required this.area,
    required this.chance,
    required this.conditions,
    required this.location,
    required this.maxLevel,
    required this.method,
    required this.methodName,
    required this.minLevel,
    required this.region,
  });
  
  factory EncounterOut.fromJson(Map<String, Object?> json) => _$EncounterOutFromJson(json);
  
  final String? area;
  final int? chance;
  final String? conditions;
  final String location;
  @JsonKey(name: 'max_level')
  final int maxLevel;
  final String method;
  @JsonKey(name: 'method_name')
  final String methodName;
  @JsonKey(name: 'min_level')
  final int minLevel;
  final String? region;

  Map<String, Object?> toJson() => _$EncounterOutToJson(this);
}
