// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'type_threat.g.dart';

/// Per attacking type: ``weak`` is weighted (a 4× weakness counts 2);.
/// ``members``/``quad`` are plain counts.
@JsonSerializable()
class TypeThreat {
  const TypeThreat({
    required this.members,
    required this.problem,
    required this.quad,
    required this.resist,
    required this.type,
    required this.weak,
  });
  
  factory TypeThreat.fromJson(Map<String, Object?> json) => _$TypeThreatFromJson(json);
  
  final int members;
  final bool problem;
  final int quad;
  final int resist;
  final String type;
  final int weak;

  Map<String, Object?> toJson() => _$TypeThreatToJson(this);
}
