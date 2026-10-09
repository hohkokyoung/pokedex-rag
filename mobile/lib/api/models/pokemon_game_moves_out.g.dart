// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pokemon_game_moves_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PokemonGameMovesOut _$PokemonGameMovesOutFromJson(Map<String, dynamic> json) =>
    PokemonGameMovesOut(
      games: (json['games'] as List<dynamic>)
          .map((e) => PokemonGameOut.fromJson(e as Map<String, dynamic>))
          .toList(),
      moves: (json['moves'] as List<dynamic>)
          .map((e) => GameMoveOut.fromJson(e as Map<String, dynamic>))
          .toList(),
      versionGroupId: (json['version_group_id'] as num?)?.toInt(),
    );

Map<String, dynamic> _$PokemonGameMovesOutToJson(
  PokemonGameMovesOut instance,
) => <String, dynamic>{
  'games': instance.games,
  'moves': instance.moves,
  'version_group_id': instance.versionGroupId,
};
