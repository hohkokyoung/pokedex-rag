// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'duel_event.dart';
import 'duel_out_first.dart';
import 'duel_out_outcome.dart';

part 'duel_out.g.dart';

@JsonSerializable()
class DuelOut {
  const DuelOut({
    required this.first,
    required this.ourName,
    required this.ourSlot,
    required this.outcome,
    required this.theirName,
    required this.theirSlot,
    this.ourSetup,
    this.theirSetup,
    this.log = const [],
    this.notes = const [],
    this.ourMoves = const [],
    this.ourMovesLearned = const [],
    this.theirMoves = const [],
    this.theirMovesLearned = const [],
  });
  
  factory DuelOut.fromJson(Map<String, Object?> json) => _$DuelOutFromJson(json);
  
  final DuelOutFirst first;
  final List<DuelEvent> log;
  final List<String> notes;
  @JsonKey(name: 'our_moves')
  final List<String> ourMoves;
  @JsonKey(name: 'our_moves_learned')
  final List<String> ourMovesLearned;
  @JsonKey(name: 'our_name')
  final String ourName;
  @JsonKey(name: 'our_setup')
  final String? ourSetup;
  @JsonKey(name: 'our_slot')
  final int ourSlot;
  final DuelOutOutcome outcome;
  @JsonKey(name: 'their_moves')
  final List<String> theirMoves;
  @JsonKey(name: 'their_moves_learned')
  final List<String> theirMovesLearned;
  @JsonKey(name: 'their_name')
  final String theirName;
  @JsonKey(name: 'their_setup')
  final String? theirSetup;
  @JsonKey(name: 'their_slot')
  final int theirSlot;

  Map<String, Object?> toJson() => _$DuelOutToJson(this);
}
