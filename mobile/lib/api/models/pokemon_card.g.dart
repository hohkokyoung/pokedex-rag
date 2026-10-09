// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pokemon_card.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PokemonCard _$PokemonCardFromJson(Map<String, dynamic> json) => PokemonCard(
  name: json['name'] as String,
  coverage: (json['coverage'] as List<dynamic>?)
      ?.map((e) => Map<String, String>.from(e as Map))
      .toList(),
  dexNumber: (json['dex_number'] as num?)?.toInt(),
  entry: json['entry'] as String?,
  match: json['match'] as num?,
  pokemonId: (json['pokemon_id'] as num?)?.toInt(),
  ref: (json['ref'] as num?)?.toInt(),
  stats: (json['stats'] as Map<String, dynamic>?)?.map(
    (k, e) => MapEntry(k, (e as num).toInt()),
  ),
  total: (json['total'] as num?)?.toInt(),
  types: (json['types'] as List<dynamic>?)?.map((e) => e as String).toList(),
  via: json['via'] as String?,
);

Map<String, dynamic> _$PokemonCardToJson(PokemonCard instance) =>
    <String, dynamic>{
      'coverage': instance.coverage,
      'dex_number': instance.dexNumber,
      'entry': instance.entry,
      'match': instance.match,
      'name': instance.name,
      'pokemon_id': instance.pokemonId,
      'ref': instance.ref,
      'stats': instance.stats,
      'total': instance.total,
      'types': instance.types,
      'via': instance.via,
    };
