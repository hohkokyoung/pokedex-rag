// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'slot_move.g.dart';

@JsonSerializable()
class SlotMove {
  const SlotMove({
    required this.moveId,
    required this.name,
    this.priority = 0,
    this.accuracy,
    this.damageClass,
    this.power,
    this.type,
  });
  
  factory SlotMove.fromJson(Map<String, Object?> json) => _$SlotMoveFromJson(json);
  
  final int? accuracy;
  @JsonKey(name: 'damage_class')
  final String? damageClass;
  @JsonKey(name: 'move_id')
  final int moveId;
  final String name;
  final int? power;
  final int priority;
  final String? type;

  Map<String, Object?> toJson() => _$SlotMoveToJson(this);
}
