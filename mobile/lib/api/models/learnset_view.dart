// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'learn_group.dart';
import 'pokemon_card.dart';

part 'learnset_view.g.dart';

/// A Pokémon's moves, grouped by how it learns them.
@JsonSerializable()
class LearnsetView {
  const LearnsetView({
    required this.groups,
    required this.pokemon,
    this.kind = 'learnset',
    this.chunkRefs,
    this.game,
    this.step,
  });
  
  factory LearnsetView.fromJson(Map<String, Object?> json) => _$LearnsetViewFromJson(json);
  
  @JsonKey(name: 'chunk_refs')
  final List<int>? chunkRefs;
  final String? game;
  final List<LearnGroup> groups;
  final String kind;
  final PokemonCard pokemon;
  final String? step;

  Map<String, Object?> toJson() => _$LearnsetViewToJson(this);
}
