// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'learnset_view.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

LearnsetView _$LearnsetViewFromJson(Map<String, dynamic> json) => LearnsetView(
  groups: (json['groups'] as List<dynamic>)
      .map((e) => LearnGroup.fromJson(e as Map<String, dynamic>))
      .toList(),
  pokemon: PokemonCard.fromJson(json['pokemon'] as Map<String, dynamic>),
  kind: json['kind'] as String? ?? 'learnset',
  chunkRefs: (json['chunk_refs'] as List<dynamic>?)
      ?.map((e) => (e as num).toInt())
      .toList(),
  game: json['game'] as String?,
  step: json['step'] as String?,
);

Map<String, dynamic> _$LearnsetViewToJson(LearnsetView instance) =>
    <String, dynamic>{
      'chunk_refs': instance.chunkRefs,
      'game': instance.game,
      'groups': instance.groups,
      'kind': instance.kind,
      'pokemon': instance.pokemon,
      'step': instance.step,
    };
