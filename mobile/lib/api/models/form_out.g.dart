// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'form_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

FormOut _$FormOutFromJson(Map<String, dynamic> json) => FormOut(
  category: json['category'] as String,
  id: (json['id'] as num).toInt(),
  matchups: MatchupsOut.fromJson(json['matchups'] as Map<String, dynamic>),
  name: json['name'] as String,
  spriteUrl: json['sprite_url'] as String,
  stats: StatsOut.fromJson(json['stats'] as Map<String, dynamic>),
  formIdentifier: json['form_identifier'] as String?,
  heightM: json['height_m'] as num?,
  spinGuide: json['spin_guide'] == null
      ? null
      : SpinGuide.fromJson(json['spin_guide'] as Map<String, dynamic>),
  weightKg: json['weight_kg'] as num?,
  abilities:
      (json['abilities'] as List<dynamic>?)
          ?.map((e) => FormAbilityOut.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  evolutionMembers:
      (json['evolution_members'] as List<dynamic>?)
          ?.map((e) => EvolutionMember.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  evolutionStages:
      (json['evolution_stages'] as List<dynamic>?)
          ?.map((e) => EvolutionStage.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  flavorEntries:
      (json['flavor_entries'] as List<dynamic>?)
          ?.map((e) => FlavorEntry.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  flavorTexts:
      (json['flavor_texts'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  isBattleOnly: json['is_battle_only'] as bool? ?? false,
  isGigantamax: json['is_gigantamax'] as bool? ?? false,
  isMega: json['is_mega'] as bool? ?? false,
  types:
      (json['types'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
);

Map<String, dynamic> _$FormOutToJson(FormOut instance) => <String, dynamic>{
  'abilities': instance.abilities,
  'category': instance.category,
  'evolution_members': instance.evolutionMembers,
  'evolution_stages': instance.evolutionStages,
  'flavor_entries': instance.flavorEntries,
  'flavor_texts': instance.flavorTexts,
  'form_identifier': instance.formIdentifier,
  'height_m': instance.heightM,
  'id': instance.id,
  'is_battle_only': instance.isBattleOnly,
  'is_gigantamax': instance.isGigantamax,
  'is_mega': instance.isMega,
  'matchups': instance.matchups,
  'name': instance.name,
  'spin_guide': instance.spinGuide,
  'sprite_url': instance.spriteUrl,
  'stats': instance.stats,
  'types': instance.types,
  'weight_kg': instance.weightKg,
};
