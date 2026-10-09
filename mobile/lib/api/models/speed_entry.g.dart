// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'speed_entry.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SpeedEntry _$SpeedEntryFromJson(Map<String, dynamic> json) => SpeedEntry(
  name: json['name'] as String,
  speed: (json['speed'] as num).toInt(),
  sprite: json['sprite'] as String,
);

Map<String, dynamic> _$SpeedEntryToJson(SpeedEntry instance) =>
    <String, dynamic>{
      'name': instance.name,
      'speed': instance.speed,
      'sprite': instance.sprite,
    };
