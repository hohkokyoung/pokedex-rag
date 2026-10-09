// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'move_row.g.dart';

@JsonSerializable()
class MoveRow {
  const MoveRow({
    required this.name,
    required this.type,
    this.accuracy,
    this.damageClass,
    this.effect,
    this.learners,
    this.moveId,
    this.power,
    this.pp,
    this.ref,
  });
  
  factory MoveRow.fromJson(Map<String, Object?> json) => _$MoveRowFromJson(json);
  
  final int? accuracy;
  @JsonKey(name: 'damage_class')
  final String? damageClass;
  final String? effect;
  final int? learners;
  @JsonKey(name: 'move_id')
  final int? moveId;
  final String name;
  final int? power;
  final int? pp;
  final int? ref;
  final String type;

  Map<String, Object?> toJson() => _$MoveRowToJson(this);
}
