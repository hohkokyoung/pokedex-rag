// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'learn_move.g.dart';

@JsonSerializable()
class LearnMove {
  const LearnMove({
    required this.name,
    required this.type,
    this.damageClass,
    this.level,
    this.levelNote,
    this.power,
  });
  
  factory LearnMove.fromJson(Map<String, Object?> json) => _$LearnMoveFromJson(json);
  
  @JsonKey(name: 'damage_class')
  final String? damageClass;
  final int? level;
  @JsonKey(name: 'level_note')
  final String? levelNote;
  final String name;
  final int? power;
  final String type;

  Map<String, Object?> toJson() => _$LearnMoveToJson(this);
}
