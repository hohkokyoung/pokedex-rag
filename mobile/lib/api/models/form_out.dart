// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'evolution_member.dart';
import 'evolution_stage.dart';
import 'flavor_entry.dart';
import 'form_ability_out.dart';
import 'matchups_out.dart';
import 'spin_guide.dart';
import 'stats_out.dart';

part 'form_out.g.dart';

/// An alternate form of a species. Carries everything the detail page's form.
/// switcher swaps in (sprite/name/types/stats/abilities/matchups); species-level.
/// moveset stays on the base species, but evolution and dex-entry flavor are now.
/// per-form (a form may have its own evolution chain and/or flavor text).
@JsonSerializable()
class FormOut {
  const FormOut({
    required this.category,
    required this.id,
    required this.matchups,
    required this.name,
    required this.spriteUrl,
    required this.stats,
    this.formIdentifier,
    this.heightM,
    this.spinGuide,
    this.weightKg,
    this.abilities = const [],
    this.evolutionMembers = const [],
    this.evolutionStages = const [],
    this.flavorEntries = const [],
    this.flavorTexts = const [],
    this.isBattleOnly = false,
    this.isGigantamax = false,
    this.isMega = false,
    this.types = const [],
  });
  
  factory FormOut.fromJson(Map<String, Object?> json) => _$FormOutFromJson(json);
  
  final List<FormAbilityOut> abilities;
  final String category;
  @JsonKey(name: 'evolution_members')
  final List<EvolutionMember> evolutionMembers;
  @JsonKey(name: 'evolution_stages')
  final List<EvolutionStage> evolutionStages;
  @JsonKey(name: 'flavor_entries')
  final List<FlavorEntry> flavorEntries;
  @JsonKey(name: 'flavor_texts')
  final List<String> flavorTexts;
  @JsonKey(name: 'form_identifier')
  final String? formIdentifier;
  @JsonKey(name: 'height_m')
  final num? heightM;
  final int id;
  @JsonKey(name: 'is_battle_only')
  final bool isBattleOnly;
  @JsonKey(name: 'is_gigantamax')
  final bool isGigantamax;
  @JsonKey(name: 'is_mega')
  final bool isMega;
  final MatchupsOut matchups;
  final String name;
  @JsonKey(name: 'spin_guide')
  final SpinGuide? spinGuide;
  @JsonKey(name: 'sprite_url')
  final String spriteUrl;
  final StatsOut stats;
  final List<String> types;
  @JsonKey(name: 'weight_kg')
  final num? weightKg;

  Map<String, Object?> toJson() => _$FormOutToJson(this);
}
