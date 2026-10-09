// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'speed_entry.dart';
import 'team_profile_lean.dart';
import 'type_net.dart';

part 'team_profile.g.dart';

/// "What kind of team is this?" at a glance, from stats as built.
@JsonSerializable()
class TeamProfile {
  const TeamProfile({
    required this.avg,
    required this.avgBst,
    required this.avgSpeed,
    required this.coreTypes,
    required this.fastCount,
    required this.gist,
    required this.items,
    required this.lean,
    required this.movesSet,
    required this.physical,
    required this.priority,
    required this.resists,
    required this.special,
    required this.speeds,
    required this.strongVs,
    required this.style,
    required this.styleWhy,
    required this.weakTo,
  });
  
  factory TeamProfile.fromJson(Map<String, Object?> json) => _$TeamProfileFromJson(json);
  
  final Map<String, int> avg;
  @JsonKey(name: 'avg_bst')
  final int avgBst;
  @JsonKey(name: 'avg_speed')
  final int avgSpeed;
  @JsonKey(name: 'core_types')
  final List<String> coreTypes;
  @JsonKey(name: 'fast_count')
  final int fastCount;
  final String gist;
  final int items;
  final TeamProfileLean lean;
  @JsonKey(name: 'moves_set')
  final int movesSet;
  final int physical;
  final int priority;
  final List<TypeNet> resists;
  final int special;
  final List<SpeedEntry> speeds;
  @JsonKey(name: 'strong_vs')
  final List<String> strongVs;
  final String style;
  @JsonKey(name: 'style_why')
  final String styleWhy;
  @JsonKey(name: 'weak_to')
  final List<TypeNet> weakTo;

  Map<String, Object?> toJson() => _$TeamProfileToJson(this);
}
