// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'team_update.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TeamUpdate _$TeamUpdateFromJson(Map<String, dynamic> json) => TeamUpdate(
  kind: json['kind'] as String?,
  name: json['name'] as String?,
  notes: json['notes'] as String?,
);

Map<String, dynamic> _$TeamUpdateToJson(TeamUpdate instance) =>
    <String, dynamic>{
      'kind': instance.kind,
      'name': instance.name,
      'notes': instance.notes,
    };
