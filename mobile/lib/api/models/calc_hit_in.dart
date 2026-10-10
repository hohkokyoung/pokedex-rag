// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'calc_hit_in.g.dart';

/// A hit the calculator currently shows (its own turn result, used as-is).
@JsonSerializable()
class CalcHitIn {
  const CalcHitIn({
    required this.attacker,
    required this.maxPct,
    required this.minPct,
    required this.move,
    required this.target,
    this.ko = 0,
    this.te = 1,
  });
  
  factory CalcHitIn.fromJson(Map<String, Object?> json) => _$CalcHitInFromJson(json);
  
  final int attacker;
  final int ko;
  @JsonKey(name: 'max_pct')
  final num maxPct;
  @JsonKey(name: 'min_pct')
  final num minPct;
  final String move;
  final int target;
  final num te;

  Map<String, Object?> toJson() => _$CalcHitInToJson(this);
}
