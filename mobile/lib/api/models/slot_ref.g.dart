// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'slot_ref.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SlotRef _$SlotRefFromJson(Map<String, dynamic> json) =>
    SlotRef(name: json['name'] as String, slot: (json['slot'] as num).toInt());

Map<String, dynamic> _$SlotRefToJson(SlotRef instance) => <String, dynamic>{
  'name': instance.name,
  'slot': instance.slot,
};
