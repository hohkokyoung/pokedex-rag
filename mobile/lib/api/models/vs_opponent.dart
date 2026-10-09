// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'matchup_cell.dart';
import 'opponent_threat.dart';
import 'pressure_point.dart';
import 'score_row.dart';
import 'verdict.dart';
import 'vs_member.dart';

part 'vs_opponent.g.dart';

@JsonSerializable()
class VsOpponent {
  const VsOpponent({
    required this.advice,
    required this.opponentId,
    required this.opponentName,
    required this.threats,
    this.verdict,
    this.cells = const [],
    this.ourMembers = const [],
    this.ourPressure = const [],
    this.scorecard = const [],
    this.theirMembers = const [],
  });
  
  factory VsOpponent.fromJson(Map<String, Object?> json) => _$VsOpponentFromJson(json);
  
  final List<String> advice;
  final List<MatchupCell> cells;
  @JsonKey(name: 'opponent_id')
  final int opponentId;
  @JsonKey(name: 'opponent_name')
  final String opponentName;
  @JsonKey(name: 'our_members')
  final List<VsMember> ourMembers;
  @JsonKey(name: 'our_pressure')
  final List<PressurePoint> ourPressure;
  final List<ScoreRow> scorecard;
  @JsonKey(name: 'their_members')
  final List<VsMember> theirMembers;
  final List<OpponentThreat> threats;
  final Verdict? verdict;

  Map<String, Object?> toJson() => _$VsOpponentToJson(this);
}
