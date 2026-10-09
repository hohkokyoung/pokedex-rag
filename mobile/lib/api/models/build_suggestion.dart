// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'build_suggestion.g.dart';

@JsonSerializable()
class BuildSuggestion {
  const BuildSuggestion({
    required this.evs,
    required this.moves,
    required this.pokemon,
    this.why = '',
    this.ability,
    this.item,
    this.nature,
  });
  
  factory BuildSuggestion.fromJson(Map<String, Object?> json) => _$BuildSuggestionFromJson(json);
  
  final String? ability;
  final Map<String, int> evs;
  final String? item;
  final List<String> moves;
  final String? nature;
  final String pokemon;
  final String why;

  Map<String, Object?> toJson() => _$BuildSuggestionToJson(this);
}
