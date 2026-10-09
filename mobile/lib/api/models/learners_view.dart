// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'move_row.dart';
import 'pokemon_card.dart';

part 'learners_view.g.dart';

/// Who learns a move: how many, by which method, and the standout users.
@JsonSerializable()
class LearnersView {
  const LearnersView({
    required this.move,
    required this.rows,
    required this.total,
    this.kind = 'learners',
    this.byMethod,
    this.chunkRefs,
    this.game,
    this.maxLevel,
    this.method,
    this.scope,
    this.step,
  });
  
  factory LearnersView.fromJson(Map<String, Object?> json) => _$LearnersViewFromJson(json);
  
  @JsonKey(name: 'by_method')
  final Map<String, int>? byMethod;
  @JsonKey(name: 'chunk_refs')
  final List<int>? chunkRefs;
  final String? game;
  final String kind;
  @JsonKey(name: 'max_level')
  final int? maxLevel;
  final String? method;
  final MoveRow move;
  final List<PokemonCard> rows;
  final List<String>? scope;
  final String? step;
  final int total;

  Map<String, Object?> toJson() => _$LearnersViewToJson(this);
}
