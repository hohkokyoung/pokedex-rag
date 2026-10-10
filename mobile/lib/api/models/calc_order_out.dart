// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'calc_order_out.g.dart';

@JsonSerializable()
class CalcOrderOut {
  const CalcOrderOut({
    required this.priority,
    required this.slot,
    required this.speed,
  });
  
  factory CalcOrderOut.fromJson(Map<String, Object?> json) => _$CalcOrderOutFromJson(json);
  
  final int priority;
  final int slot;
  final int speed;

  Map<String, Object?> toJson() => _$CalcOrderOutToJson(this);
}
