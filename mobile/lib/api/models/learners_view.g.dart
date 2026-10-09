// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'learners_view.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

LearnersView _$LearnersViewFromJson(Map<String, dynamic> json) => LearnersView(
  move: MoveRow.fromJson(json['move'] as Map<String, dynamic>),
  rows: (json['rows'] as List<dynamic>)
      .map((e) => PokemonCard.fromJson(e as Map<String, dynamic>))
      .toList(),
  total: (json['total'] as num).toInt(),
  kind: json['kind'] as String? ?? 'learners',
  byMethod: (json['by_method'] as Map<String, dynamic>?)?.map(
    (k, e) => MapEntry(k, (e as num).toInt()),
  ),
  chunkRefs: (json['chunk_refs'] as List<dynamic>?)
      ?.map((e) => (e as num).toInt())
      .toList(),
  game: json['game'] as String?,
  maxLevel: (json['max_level'] as num?)?.toInt(),
  method: json['method'] as String?,
  scope: (json['scope'] as List<dynamic>?)?.map((e) => e as String).toList(),
  step: json['step'] as String?,
);

Map<String, dynamic> _$LearnersViewToJson(LearnersView instance) =>
    <String, dynamic>{
      'by_method': instance.byMethod,
      'chunk_refs': instance.chunkRefs,
      'game': instance.game,
      'kind': instance.kind,
      'max_level': instance.maxLevel,
      'method': instance.method,
      'move': instance.move,
      'rows': instance.rows,
      'scope': instance.scope,
      'step': instance.step,
      'total': instance.total,
    };
