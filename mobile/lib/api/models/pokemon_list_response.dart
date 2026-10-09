// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'pokemon_summary.dart';

part 'pokemon_list_response.g.dart';

@JsonSerializable()
class PokemonListResponse {
  const PokemonListResponse({
    required this.items,
    required this.limit,
    required this.offset,
    required this.total,
  });
  
  factory PokemonListResponse.fromJson(Map<String, Object?> json) => _$PokemonListResponseFromJson(json);
  
  final List<PokemonSummary> items;
  final int limit;
  final int offset;
  final int total;

  Map<String, Object?> toJson() => _$PokemonListResponseToJson(this);
}
