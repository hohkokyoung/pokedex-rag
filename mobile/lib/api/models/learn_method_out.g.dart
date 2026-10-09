// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'learn_method_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

LearnMethodOut _$LearnMethodOutFromJson(Map<String, dynamic> json) =>
    LearnMethodOut(
      method: json['method'] as String,
      level: (json['level'] as num?)?.toInt(),
      levelMax: (json['level_max'] as num?)?.toInt(),
    );

Map<String, dynamic> _$LearnMethodOutToJson(LearnMethodOut instance) =>
    <String, dynamic>{
      'level': instance.level,
      'level_max': instance.levelMax,
      'method': instance.method,
    };
