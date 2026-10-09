// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'item_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ItemOut _$ItemOutFromJson(Map<String, dynamic> json) => ItemOut(
  id: (json['id'] as num).toInt(),
  identifier: json['identifier'] as String,
  name: json['name'] as String,
  category: json['category'] as String?,
  cost: (json['cost'] as num?)?.toInt(),
  flavorText: json['flavor_text'] as String?,
  flingPower: (json['fling_power'] as num?)?.toInt(),
  shortEffect: json['short_effect'] as String?,
);

Map<String, dynamic> _$ItemOutToJson(ItemOut instance) => <String, dynamic>{
  'category': instance.category,
  'cost': instance.cost,
  'flavor_text': instance.flavorText,
  'fling_power': instance.flingPower,
  'id': instance.id,
  'identifier': instance.identifier,
  'name': instance.name,
  'short_effect': instance.shortEffect,
};
