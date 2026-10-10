// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'calc_hit_out_ko.dart';

part 'calc_hit_out.g.dart';

/// One hit of the turn: the damage range and how it ended.
@JsonSerializable()
class CalcHitOut {
  const CalcHitOut({
    required this.attack,
    required this.attacker,
    required this.baseValue,
    required this.defense,
    required this.friendlyFire,
    required this.ko,
    required this.koHits,
    required this.maxPct,
    required this.minPct,
    required this.mod,
    required this.move,
    required this.sash,
    required this.stab,
    required this.target,
    required this.te,
  });
  
  factory CalcHitOut.fromJson(Map<String, Object?> json) => _$CalcHitOutFromJson(json);
  
  final int attack;
  final int attacker;

  /// The name has been replaced because it contains a keyword. Original name: `base`.
  @JsonKey(name: 'base')
  final int baseValue;
  final int defense;
  @JsonKey(name: 'friendly_fire')
  final bool friendlyFire;
  final CalcHitOutKo? ko;
  @JsonKey(name: 'ko_hits')
  final int koHits;
  @JsonKey(name: 'max_pct')
  final num maxPct;
  @JsonKey(name: 'min_pct')
  final num minPct;
  final num mod;
  final String move;
  final bool sash;
  final num stab;
  final int target;
  final num te;

  Map<String, Object?> toJson() => _$CalcHitOutToJson(this);
}
