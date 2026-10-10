// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'move_game_out.g.dart';

/// A game and its moves (the finder's game filter): every move some Pokémon learns.
/// there, plus the Z-Moves or Max Moves of the games that had them.
@JsonSerializable()
class MoveGameOut {
  const MoveGameOut({
    required this.generation,
    required this.id,
    required this.identifier,
    required this.moveIds,
    required this.name,
  });
  
  factory MoveGameOut.fromJson(Map<String, Object?> json) => _$MoveGameOutFromJson(json);
  
  final int generation;
  final int id;
  final String identifier;
  @JsonKey(name: 'move_ids')
  final List<int> moveIds;
  final String name;

  Map<String, Object?> toJson() => _$MoveGameOutToJson(this);
}
