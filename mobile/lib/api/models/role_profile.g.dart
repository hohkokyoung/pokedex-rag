// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'role_profile.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

RoleProfile _$RoleProfileFromJson(Map<String, dynamic> json) => RoleProfile(
  members: (json['members'] as List<dynamic>)
      .map((e) => MemberRole.fromJson(e as Map<String, dynamic>))
      .toList(),
  missingRoles: (json['missing_roles'] as List<dynamic>)
      .map((e) => e as String)
      .toList(),
  notes: (json['notes'] as List<dynamic>).map((e) => e as String).toList(),
);

Map<String, dynamic> _$RoleProfileToJson(RoleProfile instance) =>
    <String, dynamic>{
      'members': instance.members,
      'missing_roles': instance.missingRoles,
      'notes': instance.notes,
    };
