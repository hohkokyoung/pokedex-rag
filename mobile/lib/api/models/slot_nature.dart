// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'slot_nature.g.dart';

@JsonSerializable()
class SlotNature {
  const SlotNature({
    required this.id,
    required this.name,
    this.decreasedStat,
    this.increasedStat,
  });
  
  factory SlotNature.fromJson(Map<String, Object?> json) => _$SlotNatureFromJson(json);
  
  @JsonKey(name: 'decreased_stat')
  final String? decreasedStat;
  final int id;
  @JsonKey(name: 'increased_stat')
  final String? increasedStat;
  final String name;

  Map<String, Object?> toJson() => _$SlotNatureToJson(this);
}
