// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'set_member.g.dart';

/// What a member's set adds beyond species + typing.
@JsonSerializable()
class SetMember {
  const SetMember({
    required this.name,
    required this.slot,
    this.movesSet = 0,
    this.priority = const [],
    this.recovery = const [],
    this.score = 0,
    this.setup = const [],
    this.support = const [],
    this.ability,
    this.abilityNote,
    this.item,
    this.itemNote,
  });
  
  factory SetMember.fromJson(Map<String, Object?> json) => _$SetMemberFromJson(json);
  
  final String? ability;
  @JsonKey(name: 'ability_note')
  final String? abilityNote;
  final String? item;
  @JsonKey(name: 'item_note')
  final String? itemNote;
  @JsonKey(name: 'moves_set')
  final int movesSet;
  final String name;
  final List<String> priority;
  final List<String> recovery;
  final int score;
  final List<String> setup;
  final int slot;
  final List<String> support;

  Map<String, Object?> toJson() => _$SetMemberToJson(this);
}
