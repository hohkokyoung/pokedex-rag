// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'cream_rule_direction.dart';

part 'cream_rule.g.dart';

@JsonSerializable()
class CreamRule {
  const CreamRule({
    required this.cream,
    required this.direction,
    required this.duration,
    required this.time,
  });
  
  factory CreamRule.fromJson(Map<String, Object?> json) => _$CreamRuleFromJson(json);
  
  final String cream;
  final CreamRuleDirection direction;
  final String duration;
  final String time;

  Map<String, Object?> toJson() => _$CreamRuleToJson(this);
}
