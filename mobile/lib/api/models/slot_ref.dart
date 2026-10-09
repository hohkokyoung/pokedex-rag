// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'slot_ref.g.dart';

@JsonSerializable()
class SlotRef {
  const SlotRef({
    required this.name,
    required this.slot,
  });
  
  factory SlotRef.fromJson(Map<String, Object?> json) => _$SlotRefFromJson(json);
  
  final String name;
  final int slot;

  Map<String, Object?> toJson() => _$SlotRefToJson(this);
}
