// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'member_role.dart';

part 'role_profile.g.dart';

@JsonSerializable()
class RoleProfile {
  const RoleProfile({
    required this.members,
    required this.missingRoles,
    required this.notes,
  });
  
  factory RoleProfile.fromJson(Map<String, Object?> json) => _$RoleProfileFromJson(json);
  
  final List<MemberRole> members;
  @JsonKey(name: 'missing_roles')
  final List<String> missingRoles;
  final List<String> notes;

  Map<String, Object?> toJson() => _$RoleProfileToJson(this);
}
