// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'catch_terms_out.g.dart';

/// The formula's terms for one ball (what the "math" line shows).
@JsonSerializable()
class CatchTermsOut {
  const CatchTermsOut({
    required this.a,
    required this.ball,
    required this.crit,
    required this.hp,
    required this.hpFactor,
    required this.lowLevel,
    required this.maxHp,
    required this.rate,
    required this.shake,
    required this.status,
  });
  
  factory CatchTermsOut.fromJson(Map<String, Object?> json) => _$CatchTermsOutFromJson(json);
  
  final num a;
  final num ball;
  final num crit;
  final int hp;
  @JsonKey(name: 'hp_factor')
  final num hpFactor;
  @JsonKey(name: 'low_level')
  final num lowLevel;
  @JsonKey(name: 'max_hp')
  final int maxHp;
  final int rate;
  final num shake;
  final num status;

  Map<String, Object?> toJson() => _$CatchTermsOutToJson(this);
}
