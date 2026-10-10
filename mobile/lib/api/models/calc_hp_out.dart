// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'calc_hp_out.g.dart';

@JsonSerializable()
class CalcHpOut {
  const CalcHpOut({
    required this.hi,
    required this.lo,
    required this.sash,
    required this.slot,
  });
  
  factory CalcHpOut.fromJson(Map<String, Object?> json) => _$CalcHpOutFromJson(json);
  
  final num hi;
  final num lo;
  final bool sash;
  final int slot;

  Map<String, Object?> toJson() => _$CalcHpOutToJson(this);
}
