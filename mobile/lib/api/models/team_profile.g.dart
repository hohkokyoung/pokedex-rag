// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'team_profile.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TeamProfile _$TeamProfileFromJson(Map<String, dynamic> json) => TeamProfile(
  avg: Map<String, int>.from(json['avg'] as Map),
  avgBst: (json['avg_bst'] as num).toInt(),
  avgSpeed: (json['avg_speed'] as num).toInt(),
  coreTypes: (json['core_types'] as List<dynamic>)
      .map((e) => e as String)
      .toList(),
  fastCount: (json['fast_count'] as num).toInt(),
  gist: json['gist'] as String,
  items: (json['items'] as num).toInt(),
  lean: TeamProfileLean.fromJson(json['lean'] as String),
  movesSet: (json['moves_set'] as num).toInt(),
  physical: (json['physical'] as num).toInt(),
  priority: (json['priority'] as num).toInt(),
  resists: (json['resists'] as List<dynamic>)
      .map((e) => TypeNet.fromJson(e as Map<String, dynamic>))
      .toList(),
  special: (json['special'] as num).toInt(),
  speeds: (json['speeds'] as List<dynamic>)
      .map((e) => SpeedEntry.fromJson(e as Map<String, dynamic>))
      .toList(),
  strongVs: (json['strong_vs'] as List<dynamic>)
      .map((e) => e as String)
      .toList(),
  style: json['style'] as String,
  styleWhy: json['style_why'] as String,
  weakTo: (json['weak_to'] as List<dynamic>)
      .map((e) => TypeNet.fromJson(e as Map<String, dynamic>))
      .toList(),
);

Map<String, dynamic> _$TeamProfileToJson(TeamProfile instance) =>
    <String, dynamic>{
      'avg': instance.avg,
      'avg_bst': instance.avgBst,
      'avg_speed': instance.avgSpeed,
      'core_types': instance.coreTypes,
      'fast_count': instance.fastCount,
      'gist': instance.gist,
      'items': instance.items,
      'lean': _$TeamProfileLeanEnumMap[instance.lean]!,
      'moves_set': instance.movesSet,
      'physical': instance.physical,
      'priority': instance.priority,
      'resists': instance.resists,
      'special': instance.special,
      'speeds': instance.speeds,
      'strong_vs': instance.strongVs,
      'style': instance.style,
      'style_why': instance.styleWhy,
      'weak_to': instance.weakTo,
    };

const _$TeamProfileLeanEnumMap = {
  TeamProfileLean.physical: 'Physical',
  TeamProfileLean.special: 'Special',
  TeamProfileLean.mixed: 'Mixed',
  TeamProfileLean.$unknown: r'$unknown',
};
