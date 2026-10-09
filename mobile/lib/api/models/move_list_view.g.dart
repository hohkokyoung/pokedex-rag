// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'move_list_view.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MoveListView _$MoveListViewFromJson(Map<String, dynamic> json) => MoveListView(
  moves: (json['moves'] as List<dynamic>)
      .map((e) => MoveRow.fromJson(e as Map<String, dynamic>))
      .toList(),
  kind: json['kind'] as String? ?? 'move_list',
  chunkRefs: (json['chunk_refs'] as List<dynamic>?)
      ?.map((e) => (e as num).toInt())
      .toList(),
  step: json['step'] as String?,
);

Map<String, dynamic> _$MoveListViewToJson(MoveListView instance) =>
    <String, dynamic>{
      'chunk_refs': instance.chunkRefs,
      'kind': instance.kind,
      'moves': instance.moves,
      'step': instance.step,
    };
