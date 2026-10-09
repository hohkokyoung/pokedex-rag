// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'pokemon_card.g.dart';

/// One Pokémon as evidence: art, types, stats, and whatever the step adds.
@JsonSerializable()
class PokemonCard {
  const PokemonCard({
    required this.name,
    this.coverage,
    this.dexNumber,
    this.entry,
    this.match,
    this.pokemonId,
    this.ref,
    this.stats,
    this.total,
    this.types,
    this.via,
  });
  
  factory PokemonCard.fromJson(Map<String, Object?> json) => _$PokemonCardFromJson(json);
  
  final List<Map<String, String>>? coverage;
  @JsonKey(name: 'dex_number')
  final int? dexNumber;
  final String? entry;
  final num? match;
  final String name;
  @JsonKey(name: 'pokemon_id')
  final int? pokemonId;
  final int? ref;
  final Map<String, int>? stats;
  final int? total;
  final List<String>? types;
  final String? via;

  Map<String, Object?> toJson() => _$PokemonCardToJson(this);
}
