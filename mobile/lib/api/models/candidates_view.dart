// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'candidate.dart';
import 'slot_ref.dart';

part 'candidates_view.g.dart';

/// Pokémon the coach suggests adding; each card adds only when clicked.
@JsonSerializable()
class CandidatesView {
  const CandidatesView({
    required this.candidates,
    required this.teamId,
    this.kind = 'candidates',
    this.teamFull = false,
    this.chunkRefs,
    this.members,
    this.step,
  });
  
  factory CandidatesView.fromJson(Map<String, Object?> json) => _$CandidatesViewFromJson(json);
  
  final List<Candidate> candidates;
  @JsonKey(name: 'chunk_refs')
  final List<int>? chunkRefs;
  final String kind;
  final List<SlotRef>? members;
  final String? step;
  @JsonKey(name: 'team_full')
  final bool teamFull;
  @JsonKey(name: 'team_id')
  final int teamId;

  Map<String, Object?> toJson() => _$CandidatesViewToJson(this);
}
