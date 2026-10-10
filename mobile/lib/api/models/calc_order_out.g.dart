// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'calc_order_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CalcOrderOut _$CalcOrderOutFromJson(Map<String, dynamic> json) => CalcOrderOut(
  priority: (json['priority'] as num).toInt(),
  slot: (json['slot'] as num).toInt(),
  speed: (json['speed'] as num).toInt(),
);

Map<String, dynamic> _$CalcOrderOutToJson(CalcOrderOut instance) =>
    <String, dynamic>{
      'priority': instance.priority,
      'slot': instance.slot,
      'speed': instance.speed,
    };
