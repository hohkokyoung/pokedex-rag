// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'ball_odds_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

BallOddsOut _$BallOddsOutFromJson(Map<String, dynamic> json) => BallOddsOut(
  id: json['id'] as String,
  name: json['name'] as String,
  p: json['p'] as num,
  sure: json['sure'] as bool,
  terms: CatchTermsOut.fromJson(json['terms'] as Map<String, dynamic>),
  throws: (json['throws'] as num?)?.toInt(),
  why: json['why'] as String,
);

Map<String, dynamic> _$BallOddsOutToJson(BallOddsOut instance) =>
    <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'p': instance.p,
      'sure': instance.sure,
      'terms': instance.terms,
      'throws': instance.throws,
      'why': instance.why,
    };
