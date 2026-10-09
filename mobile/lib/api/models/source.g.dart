// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'source.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

Source _$SourceFromJson(Map<String, dynamic> json) => Source(
  chunkType: json['chunk_type'] as String,
  n: (json['n'] as num).toInt(),
  score: json['score'] as num,
  snippet: json['snippet'] as String,
  dexNumber: (json['dex_number'] as num?)?.toInt(),
  pokemonId: (json['pokemon_id'] as num?)?.toInt(),
  pokemonName: json['pokemon_name'] as String?,
  sourceRef: json['source_ref'] as String?,
  step: json['step'] as String?,
  stepIndex: (json['step_index'] as num?)?.toInt(),
);

Map<String, dynamic> _$SourceToJson(Source instance) => <String, dynamic>{
  'chunk_type': instance.chunkType,
  'dex_number': instance.dexNumber,
  'n': instance.n,
  'pokemon_id': instance.pokemonId,
  'pokemon_name': instance.pokemonName,
  'score': instance.score,
  'snippet': instance.snippet,
  'source_ref': instance.sourceRef,
  'step': instance.step,
  'step_index': instance.stepIndex,
};
