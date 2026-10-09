// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'team_create.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TeamCreate _$TeamCreateFromJson(Map<String, dynamic> json) => TeamCreate(
  name: json['name'] as String,
  notes: json['notes'] as String?,
  kind: json['kind'] as String? ?? 'player',
);

Map<String, dynamic> _$TeamCreateToJson(TeamCreate instance) =>
    <String, dynamic>{
      'kind': instance.kind,
      'name': instance.name,
      'notes': instance.notes,
    };
