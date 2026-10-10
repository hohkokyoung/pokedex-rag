// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'ability_holder_out.g.dart';

/// A species that has a given ability (reverse ability lookup).
@JsonSerializable()
class AbilityHolderOut {
  const AbilityHolderOut({
    required this.dexNumber,
    required this.id,
    required this.name,
    required this.spriteUrl,
    required this.types,
    this.isHidden = false,
  });
  
  factory AbilityHolderOut.fromJson(Map<String, Object?> json) => _$AbilityHolderOutFromJson(json);
  
  @JsonKey(name: 'dex_number')
  final int dexNumber;
  final int id;
  @JsonKey(name: 'is_hidden')
  final bool isHidden;
  final String name;
  @JsonKey(name: 'sprite_url')
  final String spriteUrl;
  final List<String> types;

  Map<String, Object?> toJson() => _$AbilityHolderOutToJson(this);
}
