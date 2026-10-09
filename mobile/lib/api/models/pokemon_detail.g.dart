// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pokemon_detail.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PokemonDetail _$PokemonDetailFromJson(Map<String, dynamic> json) =>
    PokemonDetail(
      matchups: MatchupsOut.fromJson(json['matchups'] as Map<String, dynamic>),
      dexNumber: (json['dex_number'] as num).toInt(),
      types: (json['types'] as List<dynamic>).map((e) => e as String).toList(),
      evYield: Map<String, int>.from(json['ev_yield'] as Map),
      stats: StatsOut.fromJson(json['stats'] as Map<String, dynamic>),
      spriteUrl: json['sprite_url'] as String,
      abilities: (json['abilities'] as List<dynamic>)
          .map((e) => AbilityOut.fromJson(e as Map<String, dynamic>))
          .toList(),
      name: json['name'] as String,
      id: (json['id'] as num).toInt(),
      generation: json['generation'] == null
          ? null
          : GenerationOut.fromJson(json['generation'] as Map<String, dynamic>),
      baseExperience: (json['base_experience'] as num?)?.toInt(),
      femaleSpriteUrl: json['female_sprite_url'] as String?,
      baseHappiness: (json['base_happiness'] as num?)?.toInt(),
      flavorText: json['flavor_text'] as String?,
      spinGuide: json['spin_guide'] == null
          ? null
          : SpinGuide.fromJson(json['spin_guide'] as Map<String, dynamic>),
      captureRate: (json['capture_rate'] as num?)?.toInt(),
      genderRate: (json['gender_rate'] as num?)?.toInt(),
      heightM: json['height_m'] as num?,
      genus: json['genus'] as String?,
      growthRate: json['growth_rate'] as String?,
      habitat: json['habitat'] as String?,
      hatchCounter: (json['hatch_counter'] as num?)?.toInt(),
      weightKg: json['weight_kg'] as num?,
      evolutionChainId: (json['evolution_chain_id'] as num?)?.toInt(),
      shape: json['shape'] as String?,
      isMythical: json['is_mythical'] as bool? ?? false,
      isBaby: json['is_baby'] as bool? ?? false,
      forms:
          (json['forms'] as List<dynamic>?)
              ?.map((e) => FormOut.fromJson(e as Map<String, dynamic>))
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
      evolutionStages:
          (json['evolution_stages'] as List<dynamic>?)
              ?.map((e) => EvolutionStage.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      evolutionMembers:
          (json['evolution_members'] as List<dynamic>?)
              ?.map((e) => EvolutionMember.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      eggGroups:
          (json['egg_groups'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
      isLegendary: json['is_legendary'] as bool? ?? false,
      color: json['color'] as String?,
    );

Map<String, dynamic> _$PokemonDetailToJson(PokemonDetail instance) =>
    <String, dynamic>{
      'abilities': instance.abilities,
      'base_experience': instance.baseExperience,
      'base_happiness': instance.baseHappiness,
      'capture_rate': instance.captureRate,
      'color': instance.color,
      'dex_number': instance.dexNumber,
      'egg_groups': instance.eggGroups,
      'ev_yield': instance.evYield,
      'evolution_chain_id': instance.evolutionChainId,
      'evolution_members': instance.evolutionMembers,
      'evolution_stages': instance.evolutionStages,
      'female_sprite_url': instance.femaleSpriteUrl,
      'flavor_entries': instance.flavorEntries,
      'flavor_text': instance.flavorText,
      'flavor_texts': instance.flavorTexts,
      'forms': instance.forms,
      'gender_rate': instance.genderRate,
      'generation': instance.generation,
      'genus': instance.genus,
      'growth_rate': instance.growthRate,
      'habitat': instance.habitat,
      'hatch_counter': instance.hatchCounter,
      'height_m': instance.heightM,
      'id': instance.id,
      'is_baby': instance.isBaby,
      'is_legendary': instance.isLegendary,
      'is_mythical': instance.isMythical,
      'matchups': instance.matchups,
      'name': instance.name,
      'shape': instance.shape,
      'spin_guide': instance.spinGuide,
      'sprite_url': instance.spriteUrl,
      'stats': instance.stats,
      'types': instance.types,
      'weight_kg': instance.weightKg,
    };
