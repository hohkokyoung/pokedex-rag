// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'set_edit_view.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SetEditView _$SetEditViewFromJson(Map<String, dynamic> json) => SetEditView(
  after: BuildSet.fromJson(json['after'] as Map<String, dynamic>),
  before: BuildSet.fromJson(json['before'] as Map<String, dynamic>),
  name: json['name'] as String,
  side: SetEditViewSide.fromJson(json['side'] as String),
  slot: (json['slot'] as num).toInt(),
  teamId: (json['team_id'] as num).toInt(),
  kind: json['kind'] as String? ?? 'set_edit',
  spriteUrl: json['sprite_url'] as String? ?? '',
  why: json['why'] as String? ?? '',
  chunkRefs: (json['chunk_refs'] as List<dynamic>?)
      ?.map((e) => (e as num).toInt())
      .toList(),
  fields: json['fields'],
  member: json['member'],
  step: json['step'] as String?,
);

Map<String, dynamic> _$SetEditViewToJson(SetEditView instance) =>
    <String, dynamic>{
      'after': instance.after,
      'before': instance.before,
      'chunk_refs': instance.chunkRefs,
      'fields': instance.fields,
      'kind': instance.kind,
      'member': instance.member,
      'name': instance.name,
      'side': _$SetEditViewSideEnumMap[instance.side]!,
      'slot': instance.slot,
      'sprite_url': instance.spriteUrl,
      'step': instance.step,
      'team_id': instance.teamId,
      'why': instance.why,
    };

const _$SetEditViewSideEnumMap = {
  SetEditViewSide.ours: 'ours',
  SetEditViewSide.theirs: 'theirs',
  SetEditViewSide.$unknown: r'$unknown',
};
