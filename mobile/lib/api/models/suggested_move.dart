// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'suggested_move.g.dart';

@JsonSerializable()
class SuggestedMove {
  const SuggestedMove({
    required this.isSet,
    required this.name,
    this.damageClass,
    this.power,
    this.type,
  });
  
  factory SuggestedMove.fromJson(Map<String, Object?> json) => _$SuggestedMoveFromJson(json);
  
  @JsonKey(name: 'damage_class')
  final String? damageClass;
  @JsonKey(name: 'is_set')
  final bool isSet;
  final String name;
  final int? power;
  final String? type;

  Map<String, Object?> toJson() => _$SuggestedMoveToJson(this);
}
