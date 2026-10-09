// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'pokemon_game_out.g.dart';

@JsonSerializable()
class PokemonGameOut {
  const PokemonGameOut({
    required this.generation,
    required this.id,
    required this.identifier,
    required this.moves,
    required this.name,
  });
  
  factory PokemonGameOut.fromJson(Map<String, Object?> json) => _$PokemonGameOutFromJson(json);
  
  final int generation;
  final int id;
  final String identifier;
  final int moves;
  final String name;

  Map<String, Object?> toJson() => _$PokemonGameOutToJson(this);
}
