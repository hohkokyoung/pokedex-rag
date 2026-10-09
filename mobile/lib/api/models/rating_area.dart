// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'rating_area_grade.dart';
import 'rating_area_key.dart';

part 'rating_area.g.dart';

@JsonSerializable()
class RatingArea {
  const RatingArea({
    required this.fix,
    required this.grade,
    required this.headline,
    required this.key,
    required this.label,
    required this.score,
  });
  
  factory RatingArea.fromJson(Map<String, Object?> json) => _$RatingAreaFromJson(json);
  
  final String? fix;
  final RatingAreaGrade grade;
  final String headline;
  final RatingAreaKey key;
  final String label;
  final int score;

  Map<String, Object?> toJson() => _$RatingAreaToJson(this);
}
