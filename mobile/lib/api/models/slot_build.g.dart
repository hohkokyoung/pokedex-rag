// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'slot_build.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SlotBuild _$SlotBuildFromJson(Map<String, dynamic> json) => SlotBuild(
  ability: json['ability'] as String?,
  evs: (json['evs'] as Map<String, dynamic>?)?.map(
    (k, e) => MapEntry(k, (e as num).toInt()),
  ),
  item: json['item'] as String?,
  moves: (json['moves'] as List<dynamic>?)?.map((e) => e as String).toList(),
  nature: json['nature'] as String?,
);

Map<String, dynamic> _$SlotBuildToJson(SlotBuild instance) => <String, dynamic>{
  'ability': instance.ability,
  'evs': instance.evs,
  'item': instance.item,
  'moves': instance.moves,
  'nature': instance.nature,
};
