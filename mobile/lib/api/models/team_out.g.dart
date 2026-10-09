// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'team_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TeamOut _$TeamOutFromJson(Map<String, dynamic> json) => TeamOut(
  id: (json['id'] as num).toInt(),
  kind: json['kind'] as String,
  members: (json['members'] as List<dynamic>)
      .map((e) => TeamMemberOut.fromJson(e as Map<String, dynamic>))
      .toList(),
  name: json['name'] as String,
  notes: json['notes'] as String?,
);

Map<String, dynamic> _$TeamOutToJson(TeamOut instance) => <String, dynamic>{
  'id': instance.id,
  'kind': instance.kind,
  'members': instance.members,
  'name': instance.name,
  'notes': instance.notes,
};
