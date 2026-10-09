// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'slot_nature.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SlotNature _$SlotNatureFromJson(Map<String, dynamic> json) => SlotNature(
  id: (json['id'] as num).toInt(),
  name: json['name'] as String,
  decreasedStat: json['decreased_stat'] as String?,
  increasedStat: json['increased_stat'] as String?,
);

Map<String, dynamic> _$SlotNatureToJson(SlotNature instance) =>
    <String, dynamic>{
      'decreased_stat': instance.decreasedStat,
      'id': instance.id,
      'increased_stat': instance.increasedStat,
      'name': instance.name,
    };
