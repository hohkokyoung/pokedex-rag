// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'member_defense.g.dart';

@JsonSerializable()
class MemberDefense {
  const MemberDefense({
    required this.multipliers,
    required this.name,
    required this.slot,
    required this.types,
    required this.weakTo,
  });
  
  factory MemberDefense.fromJson(Map<String, Object?> json) => _$MemberDefenseFromJson(json);
  
  final Map<String, num> multipliers;
  final String name;
  final int slot;
  final List<String> types;
  @JsonKey(name: 'weak_to')
  final List<String> weakTo;

  Map<String, Object?> toJson() => _$MemberDefenseToJson(this);
}
