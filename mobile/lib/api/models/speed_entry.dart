// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'speed_entry.g.dart';

@JsonSerializable()
class SpeedEntry {
  const SpeedEntry({
    required this.name,
    required this.speed,
    required this.sprite,
  });
  
  factory SpeedEntry.fromJson(Map<String, Object?> json) => _$SpeedEntryFromJson(json);
  
  final String name;
  final int speed;
  final String sprite;

  Map<String, Object?> toJson() => _$SpeedEntryToJson(this);
}
