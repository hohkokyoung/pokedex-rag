// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'learn_method_out.dart';

part 'game_learner_out.g.dart';

/// A Pokémon (or alternate form) that learns a move in one game, and how.
@JsonSerializable()
class GameLearnerOut {
  const GameLearnerOut({
    required this.dexNumber,
    required this.id,
    required this.methods,
    required this.name,
    required this.spriteUrl,
    required this.types,
    this.formId,
    this.also = const [],
  });
  
  factory GameLearnerOut.fromJson(Map<String, Object?> json) => _$GameLearnerOutFromJson(json);
  
  final List<String> also;
  @JsonKey(name: 'dex_number')
  final int dexNumber;
  @JsonKey(name: 'form_id')
  final int? formId;
  final int id;
  final List<LearnMethodOut> methods;
  final String name;
  @JsonKey(name: 'sprite_url')
  final String spriteUrl;
  final List<String> types;

  Map<String, Object?> toJson() => _$GameLearnerOutToJson(this);
}
