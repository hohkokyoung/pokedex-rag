// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'member_added_view.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MemberAddedView _$MemberAddedViewFromJson(Map<String, dynamic> json) =>
    MemberAddedView(
      added: json['added'] as bool,
      card: PokemonCard.fromJson(json['card'] as Map<String, dynamic>),
      message: json['message'] as String,
      teamId: (json['team_id'] as num).toInt(),
      kind: json['kind'] as String? ?? 'member_added',
      chunkRefs: (json['chunk_refs'] as List<dynamic>?)
          ?.map((e) => (e as num).toInt())
          .toList(),
      slot: (json['slot'] as num?)?.toInt(),
      step: json['step'] as String?,
    );

Map<String, dynamic> _$MemberAddedViewToJson(MemberAddedView instance) =>
    <String, dynamic>{
      'added': instance.added,
      'card': instance.card,
      'chunk_refs': instance.chunkRefs,
      'kind': instance.kind,
      'message': instance.message,
      'slot': instance.slot,
      'step': instance.step,
      'team_id': instance.teamId,
    };
