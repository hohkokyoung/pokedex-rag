// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pokemon_list_view.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PokemonListView _$PokemonListViewFromJson(Map<String, dynamic> json) =>
    PokemonListView(
      cards: (json['cards'] as List<dynamic>)
          .map((e) => PokemonCard.fromJson(e as Map<String, dynamic>))
          .toList(),
      kind: json['kind'] as String? ?? 'pokemon_list',
      chunkRefs: (json['chunk_refs'] as List<dynamic>?)
          ?.map((e) => (e as num).toInt())
          .toList(),
      step: json['step'] as String?,
      title: json['title'] as String?,
    );

Map<String, dynamic> _$PokemonListViewToJson(PokemonListView instance) =>
    <String, dynamic>{
      'cards': instance.cards,
      'chunk_refs': instance.chunkRefs,
      'kind': instance.kind,
      'step': instance.step,
      'title': instance.title,
    };
