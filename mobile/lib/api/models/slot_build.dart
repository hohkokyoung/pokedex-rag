// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'slot_build.g.dart';

/// A set by name (moves, ability, nature, item, EVs) to apply to an existing slot.
@JsonSerializable()
class SlotBuild {
  const SlotBuild({
    this.ability,
    this.evs,
    this.item,
    this.moves,
    this.nature,
  });
  
  factory SlotBuild.fromJson(Map<String, Object?> json) => _$SlotBuildFromJson(json);
  
  final String? ability;
  final Map<String, int>? evs;
  final String? item;
  final List<String>? moves;
  final String? nature;

  Map<String, Object?> toJson() => _$SlotBuildToJson(this);
}
