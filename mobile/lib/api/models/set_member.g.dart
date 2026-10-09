// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'set_member.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SetMember _$SetMemberFromJson(Map<String, dynamic> json) => SetMember(
  name: json['name'] as String,
  slot: (json['slot'] as num).toInt(),
  movesSet: (json['moves_set'] as num?)?.toInt() ?? 0,
  priority:
      (json['priority'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
  recovery:
      (json['recovery'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
  score: (json['score'] as num?)?.toInt() ?? 0,
  setup:
      (json['setup'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
  support:
      (json['support'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
  ability: json['ability'] as String?,
  abilityNote: json['ability_note'] as String?,
  item: json['item'] as String?,
  itemNote: json['item_note'] as String?,
);

Map<String, dynamic> _$SetMemberToJson(SetMember instance) => <String, dynamic>{
  'ability': instance.ability,
  'ability_note': instance.abilityNote,
  'item': instance.item,
  'item_note': instance.itemNote,
  'moves_set': instance.movesSet,
  'name': instance.name,
  'priority': instance.priority,
  'recovery': instance.recovery,
  'score': instance.score,
  'setup': instance.setup,
  'slot': instance.slot,
  'support': instance.support,
};
