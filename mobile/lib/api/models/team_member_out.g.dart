// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'team_member_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TeamMemberOut _$TeamMemberOutFromJson(Map<String, dynamic> json) =>
    TeamMemberOut(
      baseStats: Map<String, int>.from(json['base_stats'] as Map),
      dexNumber: (json['dex_number'] as num).toInt(),
      evSpread: Map<String, int>.from(json['ev_spread'] as Map),
      finalStats: Map<String, int>.from(json['final_stats'] as Map),
      ivSpread: Map<String, int>.from(json['iv_spread'] as Map),
      moves: (json['moves'] as List<dynamic>)
          .map((e) => SlotMove.fromJson(e as Map<String, dynamic>))
          .toList(),
      name: json['name'] as String,
      pokemonId: (json['pokemon_id'] as num).toInt(),
      slot: (json['slot'] as num).toInt(),
      spriteUrl: json['sprite_url'] as String,
      types: (json['types'] as List<dynamic>).map((e) => e as String).toList(),
      ability: json['ability'] == null
          ? null
          : SlotAbility.fromJson(json['ability'] as Map<String, dynamic>),
      formId: (json['form_id'] as num?)?.toInt(),
      item: json['item'] == null
          ? null
          : SlotItem.fromJson(json['item'] as Map<String, dynamic>),
      nature: json['nature'] == null
          ? null
          : SlotNature.fromJson(json['nature'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$TeamMemberOutToJson(TeamMemberOut instance) =>
    <String, dynamic>{
      'ability': instance.ability,
      'base_stats': instance.baseStats,
      'dex_number': instance.dexNumber,
      'ev_spread': instance.evSpread,
      'final_stats': instance.finalStats,
      'form_id': instance.formId,
      'item': instance.item,
      'iv_spread': instance.ivSpread,
      'moves': instance.moves,
      'name': instance.name,
      'nature': instance.nature,
      'pokemon_id': instance.pokemonId,
      'slot': instance.slot,
      'sprite_url': instance.spriteUrl,
      'types': instance.types,
    };
