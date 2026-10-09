// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'member_role.g.dart';

@JsonSerializable()
class MemberRole {
  const MemberRole({
    required this.bst,
    required this.bulk,
    required this.name,
    required this.offense,
    required this.role,
    required this.slot,
    required this.speed,
    this.effSpeed,
    this.speedNote,
  });
  
  factory MemberRole.fromJson(Map<String, Object?> json) => _$MemberRoleFromJson(json);
  
  final int bst;
  final int bulk;
  @JsonKey(name: 'eff_speed')
  final int? effSpeed;
  final String name;
  final int offense;
  final String role;
  final int slot;
  final int speed;
  @JsonKey(name: 'speed_note')
  final String? speedNote;

  Map<String, Object?> toJson() => _$MemberRoleToJson(this);
}
