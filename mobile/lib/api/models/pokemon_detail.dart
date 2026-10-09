// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'ability_out.dart';
import 'evolution_member.dart';
import 'evolution_stage.dart';
import 'flavor_entry.dart';
import 'form_out.dart';
import 'generation_out.dart';
import 'matchups_out.dart';
import 'spin_guide.dart';
import 'stats_out.dart';

part 'pokemon_detail.g.dart';

@JsonSerializable()
class PokemonDetail {
  const PokemonDetail({
    required this.matchups,
    required this.dexNumber,
    required this.types,
    required this.evYield,
    required this.stats,
    required this.spriteUrl,
    required this.abilities,
    required this.name,
    required this.id,
    this.generation,
    this.baseExperience,
    this.femaleSpriteUrl,
    this.baseHappiness,
    this.flavorText,
    this.spinGuide,
    this.captureRate,
    this.genderRate,
    this.heightM,
    this.genus,
    this.growthRate,
    this.habitat,
    this.hatchCounter,
    this.weightKg,
    this.evolutionChainId,
    this.shape,
    this.isMythical = false,
    this.isBaby = false,
    this.forms = const [],
    this.flavorEntries = const [],
    this.flavorTexts = const [],
    this.evolutionStages = const [],
    this.evolutionMembers = const [],
    this.eggGroups = const [],
    this.isLegendary = false,
    this.color,
  });
  
  factory PokemonDetail.fromJson(Map<String, Object?> json) => _$PokemonDetailFromJson(json);
  
  final List<AbilityOut> abilities;
  @JsonKey(name: 'base_experience')
  final int? baseExperience;
  @JsonKey(name: 'base_happiness')
  final int? baseHappiness;
  @JsonKey(name: 'capture_rate')
  final int? captureRate;
  final String? color;
  @JsonKey(name: 'dex_number')
  final int dexNumber;
  @JsonKey(name: 'egg_groups')
  final List<String> eggGroups;
  @JsonKey(name: 'ev_yield')
  final Map<String, int> evYield;
  @JsonKey(name: 'evolution_chain_id')
  final int? evolutionChainId;
  @JsonKey(name: 'evolution_members')
  final List<EvolutionMember> evolutionMembers;
  @JsonKey(name: 'evolution_stages')
  final List<EvolutionStage> evolutionStages;
  @JsonKey(name: 'female_sprite_url')
  final String? femaleSpriteUrl;
  @JsonKey(name: 'flavor_entries')
  final List<FlavorEntry> flavorEntries;
  @JsonKey(name: 'flavor_text')
  final String? flavorText;
  @JsonKey(name: 'flavor_texts')
  final List<String> flavorTexts;
  final List<FormOut> forms;
  @JsonKey(name: 'gender_rate')
  final int? genderRate;
  final GenerationOut? generation;
  final String? genus;
  @JsonKey(name: 'growth_rate')
  final String? growthRate;
  final String? habitat;
  @JsonKey(name: 'hatch_counter')
  final int? hatchCounter;
  @JsonKey(name: 'height_m')
  final num? heightM;
  final int id;
  @JsonKey(name: 'is_baby')
  final bool isBaby;
  @JsonKey(name: 'is_legendary')
  final bool isLegendary;
  @JsonKey(name: 'is_mythical')
  final bool isMythical;
  final MatchupsOut matchups;
  final String name;
  final String? shape;
  @JsonKey(name: 'spin_guide')
  final SpinGuide? spinGuide;
  @JsonKey(name: 'sprite_url')
  final String spriteUrl;
  final StatsOut stats;
  final List<String> types;
  @JsonKey(name: 'weight_kg')
  final num? weightKg;

  Map<String, Object?> toJson() => _$PokemonDetailToJson(this);
}
