// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'team_update.g.dart';

@JsonSerializable()
class TeamUpdate {
  const TeamUpdate({
    this.kind,
    this.name,
    this.notes,
  });
  
  factory TeamUpdate.fromJson(Map<String, Object?> json) => _$TeamUpdateFromJson(json);
  
  final String? kind;
  final String? name;
  final String? notes;

  Map<String, Object?> toJson() => _$TeamUpdateToJson(this);
}
