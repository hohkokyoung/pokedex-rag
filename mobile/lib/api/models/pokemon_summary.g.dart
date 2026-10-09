// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pokemon_summary.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PokemonSummary _$PokemonSummaryFromJson(Map<String, dynamic> json) =>
    PokemonSummary(
      baseStatTotal: (json['base_stat_total'] as num).toInt(),
      dexNumber: (json['dex_number'] as num).toInt(),
      id: (json['id'] as num).toInt(),
      name: json['name'] as String,
      spriteUrl: json['sprite_url'] as String,
      types: (json['types'] as List<dynamic>).map((e) => e as String).toList(),
      isLegendary: json['is_legendary'] as bool? ?? false,
      isMythical: json['is_mythical'] as bool? ?? false,
      formId: (json['form_id'] as num?)?.toInt(),
      generationId: (json['generation_id'] as num?)?.toInt(),
      genus: json['genus'] as String?,
      stats: json['stats'] == null
          ? null
          : StatsOut.fromJson(json['stats'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$PokemonSummaryToJson(PokemonSummary instance) =>
    <String, dynamic>{
      'base_stat_total': instance.baseStatTotal,
      'dex_number': instance.dexNumber,
      'form_id': instance.formId,
      'generation_id': instance.generationId,
      'genus': instance.genus,
      'id': instance.id,
      'is_legendary': instance.isLegendary,
      'is_mythical': instance.isMythical,
      'name': instance.name,
      'sprite_url': instance.spriteUrl,
      'stats': instance.stats,
      'types': instance.types,
    };
