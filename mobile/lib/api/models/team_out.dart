// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'team_member_out.dart';

part 'team_out.g.dart';

@JsonSerializable()
class TeamOut {
  const TeamOut({
    required this.id,
    required this.kind,
    required this.members,
    required this.name,
    this.notes,
  });
  
  factory TeamOut.fromJson(Map<String, Object?> json) => _$TeamOutFromJson(json);
  
  final int id;
  final String kind;
  final List<TeamMemberOut> members;
  final String name;
  final String? notes;

  Map<String, Object?> toJson() => _$TeamOutToJson(this);
}
