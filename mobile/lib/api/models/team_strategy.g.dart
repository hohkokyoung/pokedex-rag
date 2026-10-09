// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'team_strategy.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TeamStrategy _$TeamStrategyFromJson(Map<String, dynamic> json) => TeamStrategy(
  axes: (json['axes'] as List<dynamic>)
      .map((e) => StrategyAxis.fromJson(e as Map<String, dynamic>))
      .toList(),
  style: json['style'] as String,
  styleReason: json['style_reason'] as String,
  teamId: (json['team_id'] as num).toInt(),
);

Map<String, dynamic> _$TeamStrategyToJson(TeamStrategy instance) =>
    <String, dynamic>{
      'axes': instance.axes,
      'style': instance.style,
      'style_reason': instance.styleReason,
      'team_id': instance.teamId,
    };
