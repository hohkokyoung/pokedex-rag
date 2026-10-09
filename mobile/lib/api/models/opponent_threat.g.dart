// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'opponent_threat.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

OpponentThreat _$OpponentThreatFromJson(Map<String, dynamic> json) =>
    OpponentThreat(
      opponentName: json['opponent_name'] as String,
      opponentTypes: (json['opponent_types'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      threatens: (json['threatens'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      via: (json['via'] as List<dynamic>).map((e) => e as String).toList(),
    );

Map<String, dynamic> _$OpponentThreatToJson(OpponentThreat instance) =>
    <String, dynamic>{
      'opponent_name': instance.opponentName,
      'opponent_types': instance.opponentTypes,
      'threatens': instance.threatens,
      'via': instance.via,
    };
