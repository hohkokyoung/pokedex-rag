// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'ask_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

AskResponse _$AskResponseFromJson(Map<String, dynamic> json) => AskResponse(
  answer: json['answer'] as String,
  planner: json['planner'] as String,
  sources: (json['sources'] as List<dynamic>)
      .map((e) => Source.fromJson(e as Map<String, dynamic>))
      .toList(),
  steps: (json['steps'] as List<dynamic>?)
      ?.map((e) => PlanStepOut.fromJson(e as Map<String, dynamic>))
      .toList(),
  usage: (json['usage'] as Map<String, dynamic>?)?.map(
    (k, e) => MapEntry(k, (e as num).toInt()),
  ),
  views: (json['views'] as List<dynamic>?)
      ?.map((e) => AskResponseViewsSealed.fromJson(e as Map<String, dynamic>))
      .toList(),
  cached: json['cached'] as bool? ?? false,
);

Map<String, dynamic> _$AskResponseToJson(AskResponse instance) =>
    <String, dynamic>{
      'answer': instance.answer,
      'cached': instance.cached,
      'planner': instance.planner,
      'sources': instance.sources,
      'steps': instance.steps,
      'usage': instance.usage,
      'views': instance.views,
    };
