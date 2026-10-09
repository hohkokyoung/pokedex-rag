// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'pokemon_card.dart';

part 'pokemon_list_view.g.dart';

@JsonSerializable()
class PokemonListView {
  const PokemonListView({
    required this.cards,
    this.kind = 'pokemon_list',
    this.chunkRefs,
    this.step,
    this.title,
  });
  
  factory PokemonListView.fromJson(Map<String, Object?> json) => _$PokemonListViewFromJson(json);
  
  final List<PokemonCard> cards;
  @JsonKey(name: 'chunk_refs')
  final List<int>? chunkRefs;
  final String kind;
  final String? step;
  final String? title;

  Map<String, Object?> toJson() => _$PokemonListViewToJson(this);
}
