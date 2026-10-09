// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'slot_item.g.dart';

@JsonSerializable()
class SlotItem {
  const SlotItem({
    required this.id,
    required this.name,
    this.category,
    this.shortEffect,
  });
  
  factory SlotItem.fromJson(Map<String, Object?> json) => _$SlotItemFromJson(json);
  
  final String? category;
  final int id;
  final String name;
  @JsonKey(name: 'short_effect')
  final String? shortEffect;

  Map<String, Object?> toJson() => _$SlotItemToJson(this);
}
