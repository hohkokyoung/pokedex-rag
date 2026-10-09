// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'source.g.dart';

@JsonSerializable()
class Source {
  const Source({
    required this.chunkType,
    required this.n,
    required this.score,
    required this.snippet,
    this.dexNumber,
    this.pokemonId,
    this.pokemonName,
    this.sourceRef,
    this.step,
    this.stepIndex,
  });
  
  factory Source.fromJson(Map<String, Object?> json) => _$SourceFromJson(json);
  
  @JsonKey(name: 'chunk_type')
  final String chunkType;
  @JsonKey(name: 'dex_number')
  final int? dexNumber;
  final int n;
  @JsonKey(name: 'pokemon_id')
  final int? pokemonId;
  @JsonKey(name: 'pokemon_name')
  final String? pokemonName;
  final num score;
  final String snippet;
  @JsonKey(name: 'source_ref')
  final String? sourceRef;
  final String? step;
  @JsonKey(name: 'step_index')
  final int? stepIndex;

  Map<String, Object?> toJson() => _$SourceToJson(this);
}
