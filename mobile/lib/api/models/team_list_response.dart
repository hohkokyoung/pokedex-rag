// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'team_summary.dart';

part 'team_list_response.g.dart';

@JsonSerializable()
class TeamListResponse {
  const TeamListResponse({
    required this.teams,
  });
  
  factory TeamListResponse.fromJson(Map<String, Object?> json) => _$TeamListResponseFromJson(json);
  
  final List<TeamSummary> teams;

  Map<String, Object?> toJson() => _$TeamListResponseToJson(this);
}
