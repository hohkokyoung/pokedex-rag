// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'candidate.g.dart';

@JsonSerializable()
class Candidate {
  const Candidate({
    required this.baseStats,
    required this.dexNumber,
    required this.name,
    required this.pokemonId,
    required this.reason,
    required this.role,
    required this.spriteUrl,
    required this.types,
  });
  
  factory Candidate.fromJson(Map<String, Object?> json) => _$CandidateFromJson(json);
  
  @JsonKey(name: 'base_stats')
  final Map<String, int> baseStats;
  @JsonKey(name: 'dex_number')
  final int dexNumber;
  final String name;
  @JsonKey(name: 'pokemon_id')
  final int pokemonId;
  final String reason;
  final String role;
  @JsonKey(name: 'sprite_url')
  final String spriteUrl;
  final List<String> types;

  Map<String, Object?> toJson() => _$CandidateToJson(this);
}
