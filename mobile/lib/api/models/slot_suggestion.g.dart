// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'slot_suggestion.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SlotSuggestion _$SlotSuggestionFromJson(Map<String, dynamic> json) =>
    SlotSuggestion(
      name: json['name'] as String,
      rationale: json['rationale'] as String,
      recommendedEvs: Map<String, int>.from(json['recommended_evs'] as Map),
      slot: (json['slot'] as num).toInt(),
      recommendedMoves:
          (json['recommended_moves'] as List<dynamic>?)
              ?.map((e) => SuggestedMove.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      abilityReason: json['ability_reason'] as String?,
      recommendedAbility: json['recommended_ability'] as String?,
      recommendedItem: json['recommended_item'] as String?,
      recommendedNature: json['recommended_nature'] as String?,
    );

Map<String, dynamic> _$SlotSuggestionToJson(SlotSuggestion instance) =>
    <String, dynamic>{
      'ability_reason': instance.abilityReason,
      'name': instance.name,
      'rationale': instance.rationale,
      'recommended_ability': instance.recommendedAbility,
      'recommended_evs': instance.recommendedEvs,
      'recommended_item': instance.recommendedItem,
      'recommended_moves': instance.recommendedMoves,
      'recommended_nature': instance.recommendedNature,
      'slot': instance.slot,
    };
