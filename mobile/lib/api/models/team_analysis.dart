// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'defensive_profile.dart';
import 'offensive_profile.dart';
import 'role_profile.dart';
import 'set_profile.dart';
import 'slot_suggestion.dart';
import 'team_profile.dart';
import 'team_rating.dart';
import 'vs_opponent.dart';

part 'team_analysis.g.dart';

@JsonSerializable()
class TeamAnalysis {
  const TeamAnalysis({
    required this.defensive,
    required this.name,
    required this.offensive,
    required this.roles,
    required this.size,
    required this.suggestions,
    required this.summary,
    required this.teamId,
    this.profile,
    this.rating,
    this.sets,
    this.vsOpponent,
  });
  
  factory TeamAnalysis.fromJson(Map<String, Object?> json) => _$TeamAnalysisFromJson(json);
  
  final DefensiveProfile defensive;
  final String name;
  final OffensiveProfile offensive;
  final TeamProfile? profile;
  final TeamRating? rating;
  final RoleProfile roles;
  final SetProfile? sets;
  final int size;
  final List<SlotSuggestion> suggestions;
  final List<String> summary;
  @JsonKey(name: 'team_id')
  final int teamId;
  @JsonKey(name: 'vs_opponent')
  final VsOpponent? vsOpponent;

  Map<String, Object?> toJson() => _$TeamAnalysisToJson(this);
}
