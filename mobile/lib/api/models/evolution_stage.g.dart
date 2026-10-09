// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'evolution_stage.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

EvolutionStage _$EvolutionStageFromJson(Map<String, dynamic> json) =>
    EvolutionStage(
      toId: (json['to_id'] as num).toInt(),
      toName: json['to_name'] as String,
      condition: json['condition'] as String?,
      display: json['display'] == null
          ? null
          : EvolutionDisplay.fromJson(json['display'] as Map<String, dynamic>),
      fromId: (json['from_id'] as num?)?.toInt(),
      fromName: json['from_name'] as String?,
      item: json['item'] as String?,
      minLevel: (json['min_level'] as num?)?.toInt(),
      trigger: json['trigger'] as String?,
    );

Map<String, dynamic> _$EvolutionStageToJson(EvolutionStage instance) =>
    <String, dynamic>{
      'condition': instance.condition,
      'display': instance.display,
      'from_id': instance.fromId,
      'from_name': instance.fromName,
      'item': instance.item,
      'min_level': instance.minLevel,
      'to_id': instance.toId,
      'to_name': instance.toName,
      'trigger': instance.trigger,
    };
