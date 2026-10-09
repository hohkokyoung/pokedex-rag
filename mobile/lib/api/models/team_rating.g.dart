// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'team_rating.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TeamRating _$TeamRatingFromJson(Map<String, dynamic> json) => TeamRating(
  areas: (json['areas'] as List<dynamic>)
      .map((e) => RatingArea.fromJson(e as Map<String, dynamic>))
      .toList(),
  capped: json['capped'] as bool,
  ceiling: (json['ceiling'] as num).toInt(),
  cover: (json['cover'] as List<dynamic>)
      .map((e) => TypeCover.fromJson(e as Map<String, dynamic>))
      .toList(),
  fastSpeed: (json['fast_speed'] as num).toInt(),
  grade: TeamRatingGrade.fromJson(json['grade'] as String),
  overall: (json['overall'] as num).toInt(),
  threats: (json['threats'] as List<dynamic>)
      .map((e) => TypeThreat.fromJson(e as Map<String, dynamic>))
      .toList(),
);

Map<String, dynamic> _$TeamRatingToJson(TeamRating instance) =>
    <String, dynamic>{
      'areas': instance.areas,
      'capped': instance.capped,
      'ceiling': instance.ceiling,
      'cover': instance.cover,
      'fast_speed': instance.fastSpeed,
      'grade': _$TeamRatingGradeEnumMap[instance.grade]!,
      'overall': instance.overall,
      'threats': instance.threats,
    };

const _$TeamRatingGradeEnumMap = {
  TeamRatingGrade.a: 'A',
  TeamRatingGrade.b: 'B',
  TeamRatingGrade.c: 'C',
  TeamRatingGrade.d: 'D',
  TeamRatingGrade.f: 'F',
  TeamRatingGrade.$unknown: r'$unknown',
};
