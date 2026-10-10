// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'build_suggestion.dart';
import 'coach_turn.dart';

part 'calc_proposal.g.dart';

@JsonSerializable()
class CalcProposal {
  const CalcProposal({
    required this.build,
    required this.slot,
    this.thread,
  });
  
  factory CalcProposal.fromJson(Map<String, Object?> json) => _$CalcProposalFromJson(json);
  
  final BuildSuggestion build;
  final int slot;
  final List<CoachTurn>? thread;

  Map<String, Object?> toJson() => _$CalcProposalToJson(this);
}
