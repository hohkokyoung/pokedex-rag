// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'calc_hit_out.dart';

part 'calc_step_out.g.dart';

@JsonSerializable()
class CalcStepOut {
  const CalcStepOut({
    required this.atRisk,
    required this.hits,
    required this.skipped,
    required this.slot,
  });
  
  factory CalcStepOut.fromJson(Map<String, Object?> json) => _$CalcStepOutFromJson(json);
  
  @JsonKey(name: 'at_risk')
  final bool atRisk;
  final List<CalcHitOut> hits;
  final bool skipped;
  final int slot;

  Map<String, Object?> toJson() => _$CalcStepOutToJson(this);
}
