// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'signature_z_out.dart';

part 'move_out.g.dart';

/// A move independent of any species (global lookup).
@JsonSerializable()
class MoveOut {
  const MoveOut({
    required this.id,
    required this.identifier,
    required this.name,
    this.priority = 0,
    this.accuracy,
    this.damageClass,
    this.power,
    this.pp,
    this.shortEffect,
    this.signatureZ,
    this.type,
  });
  
  factory MoveOut.fromJson(Map<String, Object?> json) => _$MoveOutFromJson(json);
  
  final int? accuracy;
  @JsonKey(name: 'damage_class')
  final String? damageClass;
  final int id;
  final String identifier;
  final String name;
  final int? power;
  final int? pp;
  final int priority;
  @JsonKey(name: 'short_effect')
  final String? shortEffect;
  @JsonKey(name: 'signature_z')
  final SignatureZOut? signatureZ;
  final String? type;

  Map<String, Object?> toJson() => _$MoveOutToJson(this);
}
