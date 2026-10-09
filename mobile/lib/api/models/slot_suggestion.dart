// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'suggested_move.dart';

part 'slot_suggestion.g.dart';

@JsonSerializable()
class SlotSuggestion {
  const SlotSuggestion({
    required this.name,
    required this.rationale,
    required this.recommendedEvs,
    required this.slot,
    this.recommendedMoves = const [],
    this.abilityReason,
    this.recommendedAbility,
    this.recommendedItem,
    this.recommendedNature,
  });
  
  factory SlotSuggestion.fromJson(Map<String, Object?> json) => _$SlotSuggestionFromJson(json);
  
  @JsonKey(name: 'ability_reason')
  final String? abilityReason;
  final String name;
  final String rationale;
  @JsonKey(name: 'recommended_ability')
  final String? recommendedAbility;
  @JsonKey(name: 'recommended_evs')
  final Map<String, int> recommendedEvs;
  @JsonKey(name: 'recommended_item')
  final String? recommendedItem;
  @JsonKey(name: 'recommended_moves')
  final List<SuggestedMove> recommendedMoves;
  @JsonKey(name: 'recommended_nature')
  final String? recommendedNature;
  final int slot;

  Map<String, Object?> toJson() => _$SlotSuggestionToJson(this);
}
