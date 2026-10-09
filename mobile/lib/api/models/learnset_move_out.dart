// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'learnset_move_out.g.dart';

@JsonSerializable()
class LearnsetMoveOut {
  const LearnsetMoveOut({
    required this.identifier,
    required this.moveId,
    required this.name,
    this.priority = 0,
    this.accuracy,
    this.damageClass,
    this.learnMethod,
    this.level,
    this.power,
    this.pp,
    this.shortEffect,
    this.target,
    this.type,
  });
  
  factory LearnsetMoveOut.fromJson(Map<String, Object?> json) => _$LearnsetMoveOutFromJson(json);
  
  final int? accuracy;
  @JsonKey(name: 'damage_class')
  final String? damageClass;
  final String identifier;
  @JsonKey(name: 'learn_method')
  final String? learnMethod;
  final int? level;
  @JsonKey(name: 'move_id')
  final int moveId;
  final String name;
  final int? power;
  final int? pp;
  final int priority;
  @JsonKey(name: 'short_effect')
  final String? shortEffect;
  final String? target;
  final String? type;

  Map<String, Object?> toJson() => _$LearnsetMoveOutToJson(this);
}
