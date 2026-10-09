// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'cosmetic_variant_out.g.dart';

@JsonSerializable()
class CosmeticVariantOut {
  const CosmeticVariantOut({
    required this.name,
    this.spriteUrl = '',
  });
  
  factory CosmeticVariantOut.fromJson(Map<String, Object?> json) => _$CosmeticVariantOutFromJson(json);
  
  final String name;
  @JsonKey(name: 'sprite_url')
  final String spriteUrl;

  Map<String, Object?> toJson() => _$CosmeticVariantOutToJson(this);
}
