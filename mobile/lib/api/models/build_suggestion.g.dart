// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'build_suggestion.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

BuildSuggestion _$BuildSuggestionFromJson(Map<String, dynamic> json) =>
    BuildSuggestion(
      evs: Map<String, int>.from(json['evs'] as Map),
      moves: (json['moves'] as List<dynamic>).map((e) => e as String).toList(),
      pokemon: json['pokemon'] as String,
      why: json['why'] as String? ?? '',
      ability: json['ability'] as String?,
      item: json['item'] as String?,
      nature: json['nature'] as String?,
    );

Map<String, dynamic> _$BuildSuggestionToJson(BuildSuggestion instance) =>
    <String, dynamic>{
      'ability': instance.ability,
      'evs': instance.evs,
      'item': instance.item,
      'moves': instance.moves,
      'nature': instance.nature,
      'pokemon': instance.pokemon,
      'why': instance.why,
    };
