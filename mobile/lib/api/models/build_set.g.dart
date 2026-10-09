// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'build_set.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

BuildSet _$BuildSetFromJson(Map<String, dynamic> json) => BuildSet(
  ability: json['ability'] as String?,
  evs: (json['evs'] as Map<String, dynamic>?)?.map(
    (k, e) => MapEntry(k, (e as num).toInt()),
  ),
  item: json['item'] as String?,
  moves: (json['moves'] as List<dynamic>?)?.map((e) => e as String).toList(),
  nature: json['nature'] as String?,
);

Map<String, dynamic> _$BuildSetToJson(BuildSet instance) => <String, dynamic>{
  'ability': instance.ability,
  'evs': instance.evs,
  'item': instance.item,
  'moves': instance.moves,
  'nature': instance.nature,
};
