// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'calc_apply.g.dart';

/// Calculator fields to set on one slot when the user clicks Apply.
@JsonSerializable()
class CalcApply {
  const CalcApply({
    required this.fields,
    required this.slot,
  });
  
  factory CalcApply.fromJson(Map<String, Object?> json) => _$CalcApplyFromJson(json);
  
  final dynamic fields;
  final int slot;

  Map<String, Object?> toJson() => _$CalcApplyToJson(this);
}
