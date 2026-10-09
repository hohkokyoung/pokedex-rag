// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'hit_range.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

HitRange _$HitRangeFromJson(Map<String, dynamic> json) => HitRange(
  ko: (json['ko'] as num).toInt(),
  maxPct: json['max_pct'] as num,
  minPct: json['min_pct'] as num,
  koText: json['ko_text'] as String? ?? '',
  te: json['te'] as num? ?? 1,
);

Map<String, dynamic> _$HitRangeToJson(HitRange instance) => <String, dynamic>{
  'ko': instance.ko,
  'ko_text': instance.koText,
  'max_pct': instance.maxPct,
  'min_pct': instance.minPct,
  'te': instance.te,
};
