// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'duel_event_side.dart';

part 'duel_event.g.dart';

/// One step of a played-out one-on-one (side "a" = our member, "b" = theirs).
@JsonSerializable()
class DuelEvent {
  const DuelEvent({
    required this.kind,
    required this.side,
    required this.turn,
    this.ability,
    this.boosts,
    this.hp,
    this.item,
    this.move,
    this.mult,
    this.pct,
    this.type,
  });
  
  factory DuelEvent.fromJson(Map<String, Object?> json) => _$DuelEventFromJson(json);
  
  final String? ability;
  final Map<String, int>? boosts;
  final num? hp;
  final String? item;
  final String kind;
  final String? move;
  final num? mult;
  final num? pct;
  final DuelEventSide side;
  final int turn;
  final String? type;

  Map<String, Object?> toJson() => _$DuelEventToJson(this);
}
