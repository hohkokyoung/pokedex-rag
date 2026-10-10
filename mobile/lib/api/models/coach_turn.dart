// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'coach_turn.g.dart';

/// One earlier exchange: what the user asked and what the coach replied.
@JsonSerializable()
class CoachTurn {
  const CoachTurn({
    required this.ask,
    this.reply = '',
  });
  
  factory CoachTurn.fromJson(Map<String, Object?> json) => _$CoachTurnFromJson(json);
  
  final String ask;
  final String reply;

  Map<String, Object?> toJson() => _$CoachTurnToJson(this);
}
