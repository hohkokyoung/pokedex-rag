// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'form_ability_out.g.dart';

@JsonSerializable()
class FormAbilityOut {
  const FormAbilityOut({
    required this.identifier,
    required this.name,
    this.isHidden = false,
    this.effect,
    this.id,
  });
  
  factory FormAbilityOut.fromJson(Map<String, Object?> json) => _$FormAbilityOutFromJson(json);
  
  final String? effect;
  final int? id;
  final String identifier;
  @JsonKey(name: 'is_hidden')
  final bool isHidden;
  final String name;

  Map<String, Object?> toJson() => _$FormAbilityOutToJson(this);
}
