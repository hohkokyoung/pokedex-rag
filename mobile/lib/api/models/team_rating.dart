// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'rating_area.dart';
import 'team_rating_grade.dart';
import 'type_cover.dart';
import 'type_threat.dart';

part 'team_rating.g.dart';

@JsonSerializable()
class TeamRating {
  const TeamRating({
    required this.areas,
    required this.capped,
    required this.ceiling,
    required this.cover,
    required this.fastSpeed,
    required this.grade,
    required this.overall,
    required this.threats,
  });
  
  factory TeamRating.fromJson(Map<String, Object?> json) => _$TeamRatingFromJson(json);
  
  final List<RatingArea> areas;
  final bool capped;
  final int ceiling;
  final List<TypeCover> cover;
  @JsonKey(name: 'fast_speed')
  final int fastSpeed;
  final TeamRatingGrade grade;
  final int overall;
  final List<TypeThreat> threats;

  Map<String, Object?> toJson() => _$TeamRatingToJson(this);
}
