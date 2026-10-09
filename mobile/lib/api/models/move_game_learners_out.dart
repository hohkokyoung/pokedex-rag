// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'game_learner_out.dart';
import 'game_out.dart';

part 'move_game_learners_out.g.dart';

/// Who learns a move in one game, or in any game (``version_group_id`` None,.
/// the default), plus every game it's in.
@JsonSerializable()
class MoveGameLearnersOut {
  const MoveGameLearnersOut({
    required this.games,
    required this.learners,
    required this.moveId,
    required this.total,
    required this.versionGroupId,
    this.lastMachine,
    this.lastMachineGame,
    this.machine,
  });
  
  factory MoveGameLearnersOut.fromJson(Map<String, Object?> json) => _$MoveGameLearnersOutFromJson(json);
  
  final List<GameOut> games;
  @JsonKey(name: 'last_machine')
  final String? lastMachine;
  @JsonKey(name: 'last_machine_game')
  final String? lastMachineGame;
  final List<GameLearnerOut> learners;
  final String? machine;
  @JsonKey(name: 'move_id')
  final int moveId;
  final int total;
  @JsonKey(name: 'version_group_id')
  final int? versionGroupId;

  Map<String, Object?> toJson() => _$MoveGameLearnersOutToJson(this);
}
