// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'team_summary.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TeamSummary _$TeamSummaryFromJson(Map<String, dynamic> json) => TeamSummary(
  id: (json['id'] as num).toInt(),
  kind: json['kind'] as String,
  name: json['name'] as String,
  size: (json['size'] as num).toInt(),
  sprites: (json['sprites'] as List<dynamic>).map((e) => e as String).toList(),
);

Map<String, dynamic> _$TeamSummaryToJson(TeamSummary instance) =>
    <String, dynamic>{
      'id': instance.id,
      'kind': instance.kind,
      'name': instance.name,
      'size': instance.size,
      'sprites': instance.sprites,
    };
