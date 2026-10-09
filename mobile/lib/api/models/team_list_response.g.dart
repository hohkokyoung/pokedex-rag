// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'team_list_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TeamListResponse _$TeamListResponseFromJson(Map<String, dynamic> json) =>
    TeamListResponse(
      teams: (json['teams'] as List<dynamic>)
          .map((e) => TeamSummary.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$TeamListResponseToJson(TeamListResponse instance) =>
    <String, dynamic>{'teams': instance.teams};
