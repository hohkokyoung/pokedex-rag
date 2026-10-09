// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'game_out.g.dart';

@JsonSerializable()
class GameOut {
  const GameOut({
    required this.generation,
    required this.id,
    required this.identifier,
    required this.learners,
    required this.name,
  });
  
  factory GameOut.fromJson(Map<String, Object?> json) => _$GameOutFromJson(json);
  
  final int generation;
  final int id;
  final String identifier;
  final int learners;
  final String name;

  Map<String, Object?> toJson() => _$GameOutToJson(this);
}
