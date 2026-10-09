// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'team_summary_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TeamSummaryOut _$TeamSummaryOutFromJson(Map<String, dynamic> json) =>
    TeamSummaryOut(
      source: TeamSummaryOutSource.fromJson(json['source'] as String),
      teamId: (json['team_id'] as num).toInt(),
      text: json['text'] as String,
      pending: json['pending'] as bool? ?? false,
    );

Map<String, dynamic> _$TeamSummaryOutToJson(TeamSummaryOut instance) =>
    <String, dynamic>{
      'pending': instance.pending,
      'source': _$TeamSummaryOutSourceEnumMap[instance.source]!,
      'team_id': instance.teamId,
      'text': instance.text,
    };

const _$TeamSummaryOutSourceEnumMap = {
  TeamSummaryOutSource.ai: 'ai',
  TeamSummaryOutSource.rules: 'rules',
  TeamSummaryOutSource.$unknown: r'$unknown',
};
