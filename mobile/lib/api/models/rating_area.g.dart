// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'rating_area.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

RatingArea _$RatingAreaFromJson(Map<String, dynamic> json) => RatingArea(
  fix: json['fix'] as String?,
  grade: RatingAreaGrade.fromJson(json['grade'] as String),
  headline: json['headline'] as String,
  key: RatingAreaKey.fromJson(json['key'] as String),
  label: json['label'] as String,
  score: (json['score'] as num).toInt(),
);

Map<String, dynamic> _$RatingAreaToJson(RatingArea instance) =>
    <String, dynamic>{
      'fix': instance.fix,
      'grade': _$RatingAreaGradeEnumMap[instance.grade]!,
      'headline': instance.headline,
      'key': _$RatingAreaKeyEnumMap[instance.key]!,
      'label': instance.label,
      'score': instance.score,
    };

const _$RatingAreaGradeEnumMap = {
  RatingAreaGrade.a: 'A',
  RatingAreaGrade.b: 'B',
  RatingAreaGrade.c: 'C',
  RatingAreaGrade.d: 'D',
  RatingAreaGrade.f: 'F',
  RatingAreaGrade.$unknown: r'$unknown',
};

const _$RatingAreaKeyEnumMap = {
  RatingAreaKey.coverage: 'coverage',
  RatingAreaKey.defence: 'defence',
  RatingAreaKey.speed: 'speed',
  RatingAreaKey.roles: 'roles',
  RatingAreaKey.sets: 'sets',
  RatingAreaKey.roster: 'roster',
  RatingAreaKey.$unknown: r'$unknown',
};
