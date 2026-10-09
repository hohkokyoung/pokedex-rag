// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'plan_step_out.g.dart';

/// One executed plan step with its final state.
@JsonSerializable()
class PlanStepOut {
  const PlanStepOut({
    required this.id,
    required this.tool,
    this.replan = false,
    this.state = 'pending',
    this.summary = '',
    this.why = '',
    this.args,
  });
  
  factory PlanStepOut.fromJson(Map<String, Object?> json) => _$PlanStepOutFromJson(json);
  
  final dynamic args;
  final String id;
  final bool replan;
  final String state;
  final String summary;
  final String tool;
  final String why;

  Map<String, Object?> toJson() => _$PlanStepOutToJson(this);
}
