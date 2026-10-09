// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'learn_check_view.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

LearnCheckView _$LearnCheckViewFromJson(Map<String, dynamic> json) =>
    LearnCheckView(
      move: MoveRow.fromJson(json['move'] as Map<String, dynamic>),
      ok: json['ok'] as bool,
      pokemon: PokemonCard.fromJson(json['pokemon'] as Map<String, dynamic>),
      chunkRefs: (json['chunk_refs'] as List<dynamic>?)
          ?.map((e) => (e as num).toInt())
          .toList(),
      game: json['game'] as String?,
      how: json['how'] as String?,
      maxLevel: (json['max_level'] as num?)?.toInt(),
      method: json['method'] as String?,
      step: json['step'] as String?,
      absent: json['absent'] as bool? ?? false,
      kind: json['kind'] as String? ?? 'learn_check',
    );

Map<String, dynamic> _$LearnCheckViewToJson(LearnCheckView instance) =>
    <String, dynamic>{
      'absent': instance.absent,
      'chunk_refs': instance.chunkRefs,
      'game': instance.game,
      'how': instance.how,
      'kind': instance.kind,
      'max_level': instance.maxLevel,
      'method': instance.method,
      'move': instance.move,
      'ok': instance.ok,
      'pokemon': instance.pokemon,
      'step': instance.step,
    };
