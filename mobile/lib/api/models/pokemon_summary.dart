// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'stats_out.dart';

part 'pokemon_summary.g.dart';

/// Compact representation for grid/list views.
@JsonSerializable()
class PokemonSummary {
  const PokemonSummary({
    required this.baseStatTotal,
    required this.dexNumber,
    required this.id,
    required this.name,
    required this.spriteUrl,
    required this.types,
    this.isLegendary = false,
    this.isMythical = false,
    this.formId,
    this.generationId,
    this.genus,
    this.stats,
  });
  
  factory PokemonSummary.fromJson(Map<String, Object?> json) => _$PokemonSummaryFromJson(json);
  
  @JsonKey(name: 'base_stat_total')
  final int baseStatTotal;
  @JsonKey(name: 'dex_number')
  final int dexNumber;
  @JsonKey(name: 'form_id')
  final int? formId;
  @JsonKey(name: 'generation_id')
  final int? generationId;
  final String? genus;
  final int id;
  @JsonKey(name: 'is_legendary')
  final bool isLegendary;
  @JsonKey(name: 'is_mythical')
  final bool isMythical;
  final String name;
  @JsonKey(name: 'sprite_url')
  final String spriteUrl;
  final StatsOut? stats;
  final List<String> types;

  Map<String, Object?> toJson() => _$PokemonSummaryToJson(this);
}
