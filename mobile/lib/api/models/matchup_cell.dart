// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'matchup_cell_faster.dart';
import 'matchup_cell_outcome.dart';

part 'matchup_cell.g.dart';

/// One-on-one read of our member vs an opponent member, from each side's best move.
@JsonSerializable()
class MatchupCell {
  const MatchupCell({
    required this.faster,
    required this.ourHit,
    required this.ourSlot,
    required this.outcome,
    required this.score,
    required this.theirHit,
    required this.theirSlot,
    this.ourHitType,
    this.ourMove,
    this.ourSetup,
    this.theirHitType,
    this.theirMove,
    this.theirSetup,
    this.notes = const [],
    this.ourHko = 99,
    this.ourMoveLearned = false,
    this.ourPct = 0,
    this.theirHko = 99,
    this.theirMoveLearned = false,
    this.theirPct = 0,
  });
  
  factory MatchupCell.fromJson(Map<String, Object?> json) => _$MatchupCellFromJson(json);
  
  final MatchupCellFaster faster;
  final List<String> notes;
  @JsonKey(name: 'our_hit')
  final num ourHit;
  @JsonKey(name: 'our_hit_type')
  final String? ourHitType;
  @JsonKey(name: 'our_hko')
  final int ourHko;
  @JsonKey(name: 'our_move')
  final String? ourMove;
  @JsonKey(name: 'our_move_learned')
  final bool ourMoveLearned;
  @JsonKey(name: 'our_pct')
  final num ourPct;
  @JsonKey(name: 'our_setup')
  final String? ourSetup;
  @JsonKey(name: 'our_slot')
  final int ourSlot;
  final MatchupCellOutcome outcome;
  final num score;
  @JsonKey(name: 'their_hit')
  final num theirHit;
  @JsonKey(name: 'their_hit_type')
  final String? theirHitType;
  @JsonKey(name: 'their_hko')
  final int theirHko;
  @JsonKey(name: 'their_move')
  final String? theirMove;
  @JsonKey(name: 'their_move_learned')
  final bool theirMoveLearned;
  @JsonKey(name: 'their_pct')
  final num theirPct;
  @JsonKey(name: 'their_setup')
  final String? theirSetup;
  @JsonKey(name: 'their_slot')
  final int theirSlot;

  Map<String, Object?> toJson() => _$MatchupCellToJson(this);
}
