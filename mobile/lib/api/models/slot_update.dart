// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'slot_update.g.dart';

/// Set (upsert) one slot's configuration.
@JsonSerializable()
class SlotUpdate {
  const SlotUpdate({
    required this.pokemonId,
    this.abilityId,
    this.evSpread,
    this.formId,
    this.itemId,
    this.ivSpread,
    this.moveIds,
    this.natureId,
  });
  
  factory SlotUpdate.fromJson(Map<String, Object?> json) => _$SlotUpdateFromJson(json);
  
  @JsonKey(name: 'ability_id')
  final int? abilityId;
  @JsonKey(name: 'ev_spread')
  final Map<String, int>? evSpread;
  @JsonKey(name: 'form_id')
  final int? formId;
  @JsonKey(name: 'item_id')
  final int? itemId;
  @JsonKey(name: 'iv_spread')
  final Map<String, int>? ivSpread;
  @JsonKey(name: 'move_ids')
  final List<int>? moveIds;
  @JsonKey(name: 'nature_id')
  final int? natureId;
  @JsonKey(name: 'pokemon_id')
  final int pokemonId;

  Map<String, Object?> toJson() => _$SlotUpdateToJson(this);
}
