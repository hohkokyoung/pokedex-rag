// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'learn_move.dart';

part 'learn_group.g.dart';

@JsonSerializable()
class LearnGroup {
  const LearnGroup({
    required this.label,
    required this.method,
    required this.moves,
    this.ref,
  });
  
  factory LearnGroup.fromJson(Map<String, Object?> json) => _$LearnGroupFromJson(json);
  
  final String label;
  final String method;
  final List<LearnMove> moves;
  final int? ref;

  Map<String, Object?> toJson() => _$LearnGroupToJson(this);
}
