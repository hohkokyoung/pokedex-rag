// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'cosmetic_variant_out.dart';

part 'evolution_member.g.dart';

@JsonSerializable()
class EvolutionMember {
  const EvolutionMember({
    required this.dexNumber,
    required this.id,
    required this.name,
    required this.spriteUrl,
    required this.types,
    this.variants = const [],
    this.formId,
  });
  
  factory EvolutionMember.fromJson(Map<String, Object?> json) => _$EvolutionMemberFromJson(json);
  
  @JsonKey(name: 'dex_number')
  final int dexNumber;
  @JsonKey(name: 'form_id')
  final int? formId;
  final int id;
  final String name;
  @JsonKey(name: 'sprite_url')
  final String spriteUrl;
  final List<String> types;
  final List<CosmeticVariantOut> variants;

  Map<String, Object?> toJson() => _$EvolutionMemberToJson(this);
}
