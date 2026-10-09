// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'vs_member.g.dart';

@JsonSerializable()
class VsMember {
  const VsMember({
    required this.bst,
    required this.name,
    required this.pokemonId,
    required this.role,
    required this.slot,
    required this.speed,
    required this.spriteUrl,
    required this.types,
  });
  
  factory VsMember.fromJson(Map<String, Object?> json) => _$VsMemberFromJson(json);
  
  final int bst;
  final String name;
  @JsonKey(name: 'pokemon_id')
  final int pokemonId;
  final String role;
  final int slot;
  final int speed;
  @JsonKey(name: 'sprite_url')
  final String spriteUrl;
  final List<String> types;

  Map<String, Object?> toJson() => _$VsMemberToJson(this);
}
