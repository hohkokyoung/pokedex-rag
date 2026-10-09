// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'vs_opponent.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

VsOpponent _$VsOpponentFromJson(Map<String, dynamic> json) => VsOpponent(
  advice: (json['advice'] as List<dynamic>).map((e) => e as String).toList(),
  opponentId: (json['opponent_id'] as num).toInt(),
  opponentName: json['opponent_name'] as String,
  threats: (json['threats'] as List<dynamic>)
      .map((e) => OpponentThreat.fromJson(e as Map<String, dynamic>))
      .toList(),
  verdict: json['verdict'] == null
      ? null
      : Verdict.fromJson(json['verdict'] as Map<String, dynamic>),
  cells:
      (json['cells'] as List<dynamic>?)
          ?.map((e) => MatchupCell.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  ourMembers:
      (json['our_members'] as List<dynamic>?)
          ?.map((e) => VsMember.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  ourPressure:
      (json['our_pressure'] as List<dynamic>?)
          ?.map((e) => PressurePoint.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  scorecard:
      (json['scorecard'] as List<dynamic>?)
          ?.map((e) => ScoreRow.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  theirMembers:
      (json['their_members'] as List<dynamic>?)
          ?.map((e) => VsMember.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
);

Map<String, dynamic> _$VsOpponentToJson(VsOpponent instance) =>
    <String, dynamic>{
      'advice': instance.advice,
      'cells': instance.cells,
      'opponent_id': instance.opponentId,
      'opponent_name': instance.opponentName,
      'our_members': instance.ourMembers,
      'our_pressure': instance.ourPressure,
      'scorecard': instance.scorecard,
      'their_members': instance.theirMembers,
      'threats': instance.threats,
      'verdict': instance.verdict,
    };
