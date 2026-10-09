// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'stats_out.g.dart';

@JsonSerializable()
class StatsOut {
  const StatsOut({
    required this.attack,
    required this.defense,
    required this.hp,
    required this.spAttack,
    required this.spDefense,
    required this.speed,
    required this.total,
  });
  
  factory StatsOut.fromJson(Map<String, Object?> json) => _$StatsOutFromJson(json);
  
  final int attack;
  final int defense;
  final int hp;
  @JsonKey(name: 'sp_attack')
  final int spAttack;
  @JsonKey(name: 'sp_defense')
  final int spDefense;
  final int speed;
  final int total;

  Map<String, Object?> toJson() => _$StatsOutToJson(this);
}
