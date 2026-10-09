// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'plan_step_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PlanStepOut _$PlanStepOutFromJson(Map<String, dynamic> json) => PlanStepOut(
  id: json['id'] as String,
  tool: json['tool'] as String,
  replan: json['replan'] as bool? ?? false,
  state: json['state'] as String? ?? 'pending',
  summary: json['summary'] as String? ?? '',
  why: json['why'] as String? ?? '',
  args: json['args'],
);

Map<String, dynamic> _$PlanStepOutToJson(PlanStepOut instance) =>
    <String, dynamic>{
      'args': instance.args,
      'id': instance.id,
      'replan': instance.replan,
      'state': instance.state,
      'summary': instance.summary,
      'tool': instance.tool,
      'why': instance.why,
    };
