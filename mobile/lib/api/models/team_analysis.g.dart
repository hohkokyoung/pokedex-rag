// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'team_analysis.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TeamAnalysis _$TeamAnalysisFromJson(Map<String, dynamic> json) => TeamAnalysis(
  defensive: DefensiveProfile.fromJson(
    json['defensive'] as Map<String, dynamic>,
  ),
  name: json['name'] as String,
  offensive: OffensiveProfile.fromJson(
    json['offensive'] as Map<String, dynamic>,
  ),
  roles: RoleProfile.fromJson(json['roles'] as Map<String, dynamic>),
  size: (json['size'] as num).toInt(),
  suggestions: (json['suggestions'] as List<dynamic>)
      .map((e) => SlotSuggestion.fromJson(e as Map<String, dynamic>))
      .toList(),
  summary: (json['summary'] as List<dynamic>).map((e) => e as String).toList(),
  teamId: (json['team_id'] as num).toInt(),
  profile: json['profile'] == null
      ? null
      : TeamProfile.fromJson(json['profile'] as Map<String, dynamic>),
  rating: json['rating'] == null
      ? null
      : TeamRating.fromJson(json['rating'] as Map<String, dynamic>),
  sets: json['sets'] == null
      ? null
      : SetProfile.fromJson(json['sets'] as Map<String, dynamic>),
  vsOpponent: json['vs_opponent'] == null
      ? null
      : VsOpponent.fromJson(json['vs_opponent'] as Map<String, dynamic>),
);

Map<String, dynamic> _$TeamAnalysisToJson(TeamAnalysis instance) =>
    <String, dynamic>{
      'defensive': instance.defensive,
      'name': instance.name,
      'offensive': instance.offensive,
      'profile': instance.profile,
      'rating': instance.rating,
      'roles': instance.roles,
      'sets': instance.sets,
      'size': instance.size,
      'suggestions': instance.suggestions,
      'summary': instance.summary,
      'team_id': instance.teamId,
      'vs_opponent': instance.vsOpponent,
    };
