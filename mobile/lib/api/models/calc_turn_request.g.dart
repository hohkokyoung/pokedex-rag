// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'calc_turn_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CalcTurnRequest _$CalcTurnRequestFromJson(Map<String, dynamic> json) =>
    CalcTurnRequest(
      field: json['field'] == null
          ? null
          : CalcField.fromJson(json['field'] as Map<String, dynamic>),
      slots: (json['slots'] as List<dynamic>?)
          ?.map((e) => CalcSlot.fromJson(e as Map<String, dynamic>))
          .toList(),
      doubles: json['doubles'] as bool? ?? false,
      level: (json['level'] as num?)?.toInt() ?? 100,
    );

Map<String, dynamic> _$CalcTurnRequestToJson(CalcTurnRequest instance) =>
    <String, dynamic>{
      'doubles': instance.doubles,
      'field': instance.field,
      'level': instance.level,
      'slots': instance.slots,
    };
