// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'item_out.g.dart';

@JsonSerializable()
class ItemOut {
  const ItemOut({
    required this.id,
    required this.identifier,
    required this.name,
    this.category,
    this.cost,
    this.flavorText,
    this.flingPower,
    this.shortEffect,
  });
  
  factory ItemOut.fromJson(Map<String, Object?> json) => _$ItemOutFromJson(json);
  
  final String? category;
  final int? cost;
  @JsonKey(name: 'flavor_text')
  final String? flavorText;
  @JsonKey(name: 'fling_power')
  final int? flingPower;
  final int id;
  final String identifier;
  final String name;
  @JsonKey(name: 'short_effect')
  final String? shortEffect;

  Map<String, Object?> toJson() => _$ItemOutToJson(this);
}
