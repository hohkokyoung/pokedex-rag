// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'type_threat.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TypeThreat _$TypeThreatFromJson(Map<String, dynamic> json) => TypeThreat(
  members: (json['members'] as num).toInt(),
  problem: json['problem'] as bool,
  quad: (json['quad'] as num).toInt(),
  resist: (json['resist'] as num).toInt(),
  type: json['type'] as String,
  weak: (json['weak'] as num).toInt(),
);

Map<String, dynamic> _$TypeThreatToJson(TypeThreat instance) =>
    <String, dynamic>{
      'members': instance.members,
      'problem': instance.problem,
      'quad': instance.quad,
      'resist': instance.resist,
      'type': instance.type,
      'weak': instance.weak,
    };
