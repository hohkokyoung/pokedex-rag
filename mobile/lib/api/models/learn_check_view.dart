// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'move_row.dart';
import 'pokemon_card.dart';

part 'learn_check_view.g.dart';

/// Can this Pokémon learn this move? Yes (with how) or no.
@JsonSerializable()
class LearnCheckView {
  const LearnCheckView({
    required this.move,
    required this.ok,
    required this.pokemon,
    this.chunkRefs,
    this.game,
    this.how,
    this.maxLevel,
    this.method,
    this.step,
    this.absent = false,
    this.kind = 'learn_check',
  });
  
  factory LearnCheckView.fromJson(Map<String, Object?> json) => _$LearnCheckViewFromJson(json);
  
  final bool absent;
  @JsonKey(name: 'chunk_refs')
  final List<int>? chunkRefs;
  final String? game;
  final String? how;
  final String kind;
  @JsonKey(name: 'max_level')
  final int? maxLevel;
  final String? method;
  final MoveRow move;
  final bool ok;
  final PokemonCard pokemon;
  final String? step;

  Map<String, Object?> toJson() => _$LearnCheckViewToJson(this);
}
