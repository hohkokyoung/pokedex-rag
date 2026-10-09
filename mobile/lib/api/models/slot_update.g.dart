// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'slot_update.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SlotUpdate _$SlotUpdateFromJson(Map<String, dynamic> json) => SlotUpdate(
  pokemonId: (json['pokemon_id'] as num).toInt(),
  abilityId: (json['ability_id'] as num?)?.toInt(),
  evSpread: (json['ev_spread'] as Map<String, dynamic>?)?.map(
    (k, e) => MapEntry(k, (e as num).toInt()),
  ),
  formId: (json['form_id'] as num?)?.toInt(),
  itemId: (json['item_id'] as num?)?.toInt(),
  ivSpread: (json['iv_spread'] as Map<String, dynamic>?)?.map(
    (k, e) => MapEntry(k, (e as num).toInt()),
  ),
  moveIds: (json['move_ids'] as List<dynamic>?)
      ?.map((e) => (e as num).toInt())
      .toList(),
  natureId: (json['nature_id'] as num?)?.toInt(),
);

Map<String, dynamic> _$SlotUpdateToJson(SlotUpdate instance) =>
    <String, dynamic>{
      'ability_id': instance.abilityId,
      'ev_spread': instance.evSpread,
      'form_id': instance.formId,
      'item_id': instance.itemId,
      'iv_spread': instance.ivSpread,
      'move_ids': instance.moveIds,
      'nature_id': instance.natureId,
      'pokemon_id': instance.pokemonId,
    };
