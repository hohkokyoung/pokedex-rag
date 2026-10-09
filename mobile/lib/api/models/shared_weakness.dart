// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'shared_weakness.g.dart';

@JsonSerializable()
class SharedWeakness {
  const SharedWeakness({
    required this.count,
    required this.members,
    required this.type,
  });
  
  factory SharedWeakness.fromJson(Map<String, Object?> json) => _$SharedWeaknessFromJson(json);
  
  final int count;
  final List<String> members;
  final String type;

  Map<String, Object?> toJson() => _$SharedWeaknessToJson(this);
}
