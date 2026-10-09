// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'team_summary_out_source.dart';

part 'team_summary_out.g.dart';

@JsonSerializable()
class TeamSummaryOut {
  const TeamSummaryOut({
    required this.source,
    required this.teamId,
    required this.text,
    this.pending = false,
  });
  
  factory TeamSummaryOut.fromJson(Map<String, Object?> json) => _$TeamSummaryOutFromJson(json);
  
  final bool pending;
  final TeamSummaryOutSource source;
  @JsonKey(name: 'team_id')
  final int teamId;
  final String text;

  Map<String, Object?> toJson() => _$TeamSummaryOutToJson(this);
}
