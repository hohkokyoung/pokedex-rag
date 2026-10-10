// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'ball_odds_out.dart';

part 'catch_out.g.dart';

@JsonSerializable()
class CatchOut {
  const CatchOut({
    required this.balls,
    required this.captureRate,
    required this.name,
    required this.pokemonId,
  });
  
  factory CatchOut.fromJson(Map<String, Object?> json) => _$CatchOutFromJson(json);
  
  final List<BallOddsOut> balls;
  @JsonKey(name: 'capture_rate')
  final int captureRate;
  final String name;
  @JsonKey(name: 'pokemon_id')
  final int pokemonId;

  Map<String, Object?> toJson() => _$CatchOutToJson(this);
}
