// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'calc_ask_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CalcAskRequest _$CalcAskRequestFromJson(Map<String, dynamic> json) =>
    CalcAskRequest(
      question: json['question'] as String,
      field: json['field'] == null
          ? null
          : CalcField.fromJson(json['field'] as Map<String, dynamic>),
      hits: (json['hits'] as List<dynamic>?)
          ?.map((e) => CalcHitIn.fromJson(e as Map<String, dynamic>))
          .toList(),
      proposal: json['proposal'] == null
          ? null
          : CalcProposal.fromJson(json['proposal'] as Map<String, dynamic>),
      slots: (json['slots'] as List<dynamic>?)
          ?.map((e) => CalcSlot.fromJson(e as Map<String, dynamic>))
          .toList(),
      doubles: json['doubles'] as bool? ?? false,
      focus: (json['focus'] as num?)?.toInt() ?? 0,
      level: (json['level'] as num?)?.toInt() ?? 100,
    );

Map<String, dynamic> _$CalcAskRequestToJson(CalcAskRequest instance) =>
    <String, dynamic>{
      'doubles': instance.doubles,
      'field': instance.field,
      'focus': instance.focus,
      'hits': instance.hits,
      'level': instance.level,
      'proposal': instance.proposal,
      'question': instance.question,
      'slots': instance.slots,
    };
