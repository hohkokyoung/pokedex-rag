// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'learn_method_out.g.dart';

@JsonSerializable()
class LearnMethodOut {
  const LearnMethodOut({
    required this.method,
    this.level,
    this.levelMax,
  });
  
  factory LearnMethodOut.fromJson(Map<String, Object?> json) => _$LearnMethodOutFromJson(json);
  
  final int? level;
  @JsonKey(name: 'level_max')
  final int? levelMax;
  final String method;

  Map<String, Object?> toJson() => _$LearnMethodOutToJson(this);
}
