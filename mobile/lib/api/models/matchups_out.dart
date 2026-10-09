// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'matchups_out.g.dart';

@JsonSerializable()
class MatchupsOut {
  const MatchupsOut({
    this.immune = const [],
    this.resistHalf = const [],
    this.resistQuarter = const [],
    this.weak2x = const [],
    this.weak4x = const [],
  });
  
  factory MatchupsOut.fromJson(Map<String, Object?> json) => _$MatchupsOutFromJson(json);
  
  final List<String> immune;
  @JsonKey(name: 'resist_half')
  final List<String> resistHalf;
  @JsonKey(name: 'resist_quarter')
  final List<String> resistQuarter;
  @JsonKey(name: 'weak_2x')
  final List<String> weak2x;
  @JsonKey(name: 'weak_4x')
  final List<String> weak4x;

  Map<String, Object?> toJson() => _$MatchupsOutToJson(this);
}
