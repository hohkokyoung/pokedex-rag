// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'slot_item.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SlotItem _$SlotItemFromJson(Map<String, dynamic> json) => SlotItem(
  id: (json['id'] as num).toInt(),
  name: json['name'] as String,
  category: json['category'] as String?,
  shortEffect: json['short_effect'] as String?,
);

Map<String, dynamic> _$SlotItemToJson(SlotItem instance) => <String, dynamic>{
  'category': instance.category,
  'id': instance.id,
  'name': instance.name,
  'short_effect': instance.shortEffect,
};
