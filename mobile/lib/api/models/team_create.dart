// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'team_create.g.dart';

@JsonSerializable()
class TeamCreate {
  const TeamCreate({
    required this.name,
    this.notes,
    this.kind = 'player',
  });
  
  factory TeamCreate.fromJson(Map<String, Object?> json) => _$TeamCreateFromJson(json);
  
  final String kind;
  final String name;
  final String? notes;

  Map<String, Object?> toJson() => _$TeamCreateToJson(this);
}
