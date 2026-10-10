// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'calc_slot.g.dart';

/// One filled calculator slot: 0–1 are the user's side, 2–3 the opponent's.
@JsonSerializable()
class CalcSlot {
  const CalcSlot({
    required this.pokemonId,
    required this.slot,
    this.aim,
    this.evs,
    this.formId,
    this.ivs,
    this.move,
    this.ability = 'None',
    this.hp = 100,
    this.item = 'None',
    this.name = '',
    this.nature = 'Hardy',
  });
  
  factory CalcSlot.fromJson(Map<String, Object?> json) => _$CalcSlotFromJson(json);
  
  final String ability;
  final int? aim;
  final Map<String, int>? evs;
  @JsonKey(name: 'form_id')
  final int? formId;
  final num hp;
  final String item;
  final Map<String, int>? ivs;
  final String? move;
  final String name;
  final String nature;
  @JsonKey(name: 'pokemon_id')
  final int pokemonId;
  final int slot;

  Map<String, Object?> toJson() => _$CalcSlotToJson(this);
}
