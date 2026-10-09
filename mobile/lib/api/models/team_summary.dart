// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'team_summary.g.dart';

@JsonSerializable()
class TeamSummary {
  const TeamSummary({
    required this.id,
    required this.kind,
    required this.name,
    required this.size,
    required this.sprites,
  });
  
  factory TeamSummary.fromJson(Map<String, Object?> json) => _$TeamSummaryFromJson(json);
  
  final int id;
  final String kind;
  final String name;
  final int size;
  final List<String> sprites;

  Map<String, Object?> toJson() => _$TeamSummaryToJson(this);
}
