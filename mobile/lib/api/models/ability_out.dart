// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'ability_out.g.dart';

@JsonSerializable()
class AbilityOut {
  const AbilityOut({
    required this.id,
    required this.identifier,
    required this.name,
    this.isHidden = false,
    this.effect,
    this.shortEffect,
  });
  
  factory AbilityOut.fromJson(Map<String, Object?> json) => _$AbilityOutFromJson(json);
  
  final String? effect;
  final int id;
  final String identifier;
  @JsonKey(name: 'is_hidden')
  final bool isHidden;
  final String name;
  @JsonKey(name: 'short_effect')
  final String? shortEffect;

  Map<String, Object?> toJson() => _$AbilityOutToJson(this);
}
