// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'calc_move_out.g.dart';

@JsonSerializable()
class CalcMoveOut {
  const CalcMoveOut({
    required this.damageClass,
    required this.name,
    required this.power,
    required this.priority,
    required this.slot,
    required this.target,
    required this.type,
  });
  
  factory CalcMoveOut.fromJson(Map<String, Object?> json) => _$CalcMoveOutFromJson(json);
  
  @JsonKey(name: 'damage_class')
  final String damageClass;
  final String name;
  final int power;
  final int priority;
  final int slot;
  final String? target;
  final String type;

  Map<String, Object?> toJson() => _$CalcMoveOutToJson(this);
}
