// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'catch_terms_out.dart';

part 'ball_odds_out.g.dart';

@JsonSerializable()
class BallOddsOut {
  const BallOddsOut({
    required this.id,
    required this.name,
    required this.p,
    required this.sure,
    required this.terms,
    required this.throws,
    required this.why,
  });
  
  factory BallOddsOut.fromJson(Map<String, Object?> json) => _$BallOddsOutFromJson(json);
  
  final String id;
  final String name;
  final num p;
  final bool sure;
  final CatchTermsOut terms;
  final int? throws;
  final String why;

  Map<String, Object?> toJson() => _$BallOddsOutToJson(this);
}
