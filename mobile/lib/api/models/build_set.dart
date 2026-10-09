// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'build_set.g.dart';

@JsonSerializable()
class BuildSet {
  const BuildSet({
    this.ability,
    this.evs,
    this.item,
    this.moves,
    this.nature,
  });
  
  factory BuildSet.fromJson(Map<String, Object?> json) => _$BuildSetFromJson(json);
  
  final String? ability;
  final Map<String, int>? evs;
  final String? item;
  final List<String>? moves;
  final String? nature;

  Map<String, Object?> toJson() => _$BuildSetToJson(this);
}
