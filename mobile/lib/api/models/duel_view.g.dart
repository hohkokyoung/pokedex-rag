// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'duel_view.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

DuelView _$DuelViewFromJson(Map<String, dynamic> json) => DuelView(
  duel: DuelOut.fromJson(json['duel'] as Map<String, dynamic>),
  opponentId: (json['opponent_id'] as num).toInt(),
  teamId: (json['team_id'] as num).toInt(),
  kind: json['kind'] as String? ?? 'duel',
  chunkRefs: (json['chunk_refs'] as List<dynamic>?)
      ?.map((e) => (e as num).toInt())
      .toList(),
  step: json['step'] as String?,
);

Map<String, dynamic> _$DuelViewToJson(DuelView instance) => <String, dynamic>{
  'chunk_refs': instance.chunkRefs,
  'duel': instance.duel,
  'kind': instance.kind,
  'opponent_id': instance.opponentId,
  'step': instance.step,
  'team_id': instance.teamId,
};
