// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'game_move_out.dart';
import 'pokemon_game_out.dart';

part 'pokemon_game_moves_out.g.dart';

/// A Pokémon's learnset in one game, plus every game it has a learnset in.
@JsonSerializable()
class PokemonGameMovesOut {
  const PokemonGameMovesOut({
    required this.games,
    required this.moves,
    required this.versionGroupId,
  });
  
  factory PokemonGameMovesOut.fromJson(Map<String, Object?> json) => _$PokemonGameMovesOutFromJson(json);
  
  final List<PokemonGameOut> games;
  final List<GameMoveOut> moves;
  @JsonKey(name: 'version_group_id')
  final int? versionGroupId;

  Map<String, Object?> toJson() => _$PokemonGameMovesOutToJson(this);
}
