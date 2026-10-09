// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pressure_point.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PressurePoint _$PressurePointFromJson(Map<String, dynamic> json) =>
    PressurePoint(
      attacker: json['attacker'] as String,
      attackerTypes: (json['attacker_types'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      targets: (json['targets'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      via: (json['via'] as List<dynamic>).map((e) => e as String).toList(),
    );

Map<String, dynamic> _$PressurePointToJson(PressurePoint instance) =>
    <String, dynamic>{
      'attacker': instance.attacker,
      'attacker_types': instance.attackerTypes,
      'targets': instance.targets,
      'via': instance.via,
    };
