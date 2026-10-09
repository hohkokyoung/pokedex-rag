// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'build_suggestion.dart';

part 'build_proposal_view.g.dart';

@JsonSerializable()
class BuildProposalView {
  const BuildProposalView({
    required this.build,
    required this.pokemon,
    required this.slot,
    this.kind = 'build_proposal',
    this.chunkRefs,
    this.step,
  });
  
  factory BuildProposalView.fromJson(Map<String, Object?> json) => _$BuildProposalViewFromJson(json);
  
  final BuildSuggestion build;
  @JsonKey(name: 'chunk_refs')
  final List<int>? chunkRefs;
  final String kind;
  final String pokemon;
  final int slot;
  final String? step;

  Map<String, Object?> toJson() => _$BuildProposalViewToJson(this);
}
