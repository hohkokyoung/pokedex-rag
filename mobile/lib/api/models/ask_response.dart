// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'ask_response_views_sealed.dart';
import 'plan_step_out.dart';
import 'source.dart';

part 'ask_response.g.dart';

@JsonSerializable()
class AskResponse {
  const AskResponse({
    required this.answer,
    required this.planner,
    required this.sources,
    this.steps,
    this.usage,
    this.views,
    this.cached = false,
  });
  
  factory AskResponse.fromJson(Map<String, Object?> json) => _$AskResponseFromJson(json);
  
  final String answer;
  final bool cached;
  final String planner;
  final List<Source> sources;
  final List<PlanStepOut>? steps;
  final Map<String, int>? usage;
  final List<AskResponseViewsSealed>? views;

  Map<String, Object?> toJson() => _$AskResponseToJson(this);
}
