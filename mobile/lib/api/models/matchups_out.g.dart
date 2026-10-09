// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'matchups_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MatchupsOut _$MatchupsOutFromJson(Map<String, dynamic> json) => MatchupsOut(
  immune:
      (json['immune'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
  resistHalf:
      (json['resist_half'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  resistQuarter:
      (json['resist_quarter'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  weak2x:
      (json['weak_2x'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
  weak4x:
      (json['weak_4x'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
);

Map<String, dynamic> _$MatchupsOutToJson(MatchupsOut instance) =>
    <String, dynamic>{
      'immune': instance.immune,
      'resist_half': instance.resistHalf,
      'resist_quarter': instance.resistQuarter,
      'weak_2x': instance.weak2x,
      'weak_4x': instance.weak4x,
    };
