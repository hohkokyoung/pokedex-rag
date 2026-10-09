// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'encounter_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

EncounterOut _$EncounterOutFromJson(Map<String, dynamic> json) => EncounterOut(
  area: json['area'] as String?,
  chance: (json['chance'] as num?)?.toInt(),
  conditions: json['conditions'] as String?,
  location: json['location'] as String,
  maxLevel: (json['max_level'] as num).toInt(),
  method: json['method'] as String,
  methodName: json['method_name'] as String,
  minLevel: (json['min_level'] as num).toInt(),
  region: json['region'] as String?,
);

Map<String, dynamic> _$EncounterOutToJson(EncounterOut instance) =>
    <String, dynamic>{
      'area': instance.area,
      'chance': instance.chance,
      'conditions': instance.conditions,
      'location': instance.location,
      'max_level': instance.maxLevel,
      'method': instance.method,
      'method_name': instance.methodName,
      'min_level': instance.minLevel,
      'region': instance.region,
    };
