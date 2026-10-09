// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'cream_rule.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CreamRule _$CreamRuleFromJson(Map<String, dynamic> json) => CreamRule(
  cream: json['cream'] as String,
  direction: CreamRuleDirection.fromJson(json['direction'] as String),
  duration: json['duration'] as String,
  time: json['time'] as String,
);

Map<String, dynamic> _$CreamRuleToJson(CreamRule instance) => <String, dynamic>{
  'cream': instance.cream,
  'direction': _$CreamRuleDirectionEnumMap[instance.direction]!,
  'duration': instance.duration,
  'time': instance.time,
};

const _$CreamRuleDirectionEnumMap = {
  CreamRuleDirection.clockwise: 'Clockwise',
  CreamRuleDirection.counterClockwise: 'Counter-clockwise',
  CreamRuleDirection.$unknown: r'$unknown',
};
