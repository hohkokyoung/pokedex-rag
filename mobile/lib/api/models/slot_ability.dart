// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'slot_ability.g.dart';

@JsonSerializable()
class SlotAbility {
  const SlotAbility({
    required this.id,
    required this.name,
    this.isHidden = false,
  });
  
  factory SlotAbility.fromJson(Map<String, Object?> json) => _$SlotAbilityFromJson(json);
  
  final int id;
  @JsonKey(name: 'is_hidden')
  final bool isHidden;
  final String name;

  Map<String, Object?> toJson() => _$SlotAbilityToJson(this);
}
