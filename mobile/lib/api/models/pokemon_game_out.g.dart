// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pokemon_game_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PokemonGameOut _$PokemonGameOutFromJson(Map<String, dynamic> json) =>
    PokemonGameOut(
      generation: (json['generation'] as num).toInt(),
      id: (json['id'] as num).toInt(),
      identifier: json['identifier'] as String,
      moves: (json['moves'] as num).toInt(),
      name: json['name'] as String,
    );

Map<String, dynamic> _$PokemonGameOutToJson(PokemonGameOut instance) =>
    <String, dynamic>{
      'generation': instance.generation,
      'id': instance.id,
      'identifier': instance.identifier,
      'moves': instance.moves,
      'name': instance.name,
    };
