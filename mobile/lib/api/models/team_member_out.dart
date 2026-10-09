// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'slot_ability.dart';
import 'slot_item.dart';
import 'slot_move.dart';
import 'slot_nature.dart';

part 'team_member_out.g.dart';

@JsonSerializable()
class TeamMemberOut {
  const TeamMemberOut({
    required this.baseStats,
    required this.dexNumber,
    required this.evSpread,
    required this.finalStats,
    required this.ivSpread,
    required this.moves,
    required this.name,
    required this.pokemonId,
    required this.slot,
    required this.spriteUrl,
    required this.types,
    this.ability,
    this.formId,
    this.item,
    this.nature,
  });
  
  factory TeamMemberOut.fromJson(Map<String, Object?> json) => _$TeamMemberOutFromJson(json);
  
  final SlotAbility? ability;
  @JsonKey(name: 'base_stats')
  final Map<String, int> baseStats;
  @JsonKey(name: 'dex_number')
  final int dexNumber;
  @JsonKey(name: 'ev_spread')
  final Map<String, int> evSpread;
  @JsonKey(name: 'final_stats')
  final Map<String, int> finalStats;
  @JsonKey(name: 'form_id')
  final int? formId;
  final SlotItem? item;
  @JsonKey(name: 'iv_spread')
  final Map<String, int> ivSpread;
  final List<SlotMove> moves;
  final String name;
  final SlotNature? nature;
  @JsonKey(name: 'pokemon_id')
  final int pokemonId;
  final int slot;
  @JsonKey(name: 'sprite_url')
  final String spriteUrl;
  final List<String> types;

  Map<String, Object?> toJson() => _$TeamMemberOutToJson(this);
}
