// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'calc_slot.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CalcSlot _$CalcSlotFromJson(Map<String, dynamic> json) => CalcSlot(
  pokemonId: (json['pokemon_id'] as num).toInt(),
  slot: (json['slot'] as num).toInt(),
  aim: (json['aim'] as num?)?.toInt(),
  evs: (json['evs'] as Map<String, dynamic>?)?.map(
    (k, e) => MapEntry(k, (e as num).toInt()),
  ),
  formId: (json['form_id'] as num?)?.toInt(),
  ivs: (json['ivs'] as Map<String, dynamic>?)?.map(
    (k, e) => MapEntry(k, (e as num).toInt()),
  ),
  move: json['move'] as String?,
  ability: json['ability'] as String? ?? 'None',
  hp: json['hp'] as num? ?? 100,
  item: json['item'] as String? ?? 'None',
  name: json['name'] as String? ?? '',
  nature: json['nature'] as String? ?? 'Hardy',
);

Map<String, dynamic> _$CalcSlotToJson(CalcSlot instance) => <String, dynamic>{
  'ability': instance.ability,
  'aim': instance.aim,
  'evs': instance.evs,
  'form_id': instance.formId,
  'hp': instance.hp,
  'item': instance.item,
  'ivs': instance.ivs,
  'move': instance.move,
  'name': instance.name,
  'nature': instance.nature,
  'pokemon_id': instance.pokemonId,
  'slot': instance.slot,
};
