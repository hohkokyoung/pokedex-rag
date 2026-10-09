// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'pokemon_card.dart';

part 'member_added_view.g.dart';

/// An explicit "add X": what was added where (Undo clears the slot), or why not.
@JsonSerializable()
class MemberAddedView {
  const MemberAddedView({
    required this.added,
    required this.card,
    required this.message,
    required this.teamId,
    this.kind = 'member_added',
    this.chunkRefs,
    this.slot,
    this.step,
  });
  
  factory MemberAddedView.fromJson(Map<String, Object?> json) => _$MemberAddedViewFromJson(json);
  
  final bool added;
  final PokemonCard card;
  @JsonKey(name: 'chunk_refs')
  final List<int>? chunkRefs;
  final String kind;
  final String message;
  final int? slot;
  final String? step;
  @JsonKey(name: 'team_id')
  final int teamId;

  Map<String, Object?> toJson() => _$MemberAddedViewToJson(this);
}
