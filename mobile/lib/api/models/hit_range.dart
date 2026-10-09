// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'hit_range.g.dart';

@JsonSerializable()
class HitRange {
  const HitRange({
    required this.ko,
    required this.maxPct,
    required this.minPct,
    this.koText = '',
    this.te = 1,
  });
  
  factory HitRange.fromJson(Map<String, Object?> json) => _$HitRangeFromJson(json);
  
  final int ko;
  @JsonKey(name: 'ko_text')
  final String koText;
  @JsonKey(name: 'max_pct')
  final num maxPct;
  @JsonKey(name: 'min_pct')
  final num minPct;
  final num te;

  Map<String, Object?> toJson() => _$HitRangeToJson(this);
}
