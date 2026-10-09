// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'offensive_profile.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

OffensiveProfile _$OffensiveProfileFromJson(Map<String, dynamic> json) =>
    OffensiveProfile(
      coverageTypes: (json['coverage_types'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      notSuperEffective: (json['not_super_effective'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      uncoveredTypes: (json['uncovered_types'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      usedMoveCoverage: json['used_move_coverage'] as bool,
      fromLearnset:
          (json['from_learnset'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
      tips:
          (json['tips'] as List<dynamic>?)?.map((e) => e as String).toList() ??
          const [],
    );

Map<String, dynamic> _$OffensiveProfileToJson(OffensiveProfile instance) =>
    <String, dynamic>{
      'coverage_types': instance.coverageTypes,
      'from_learnset': instance.fromLearnset,
      'not_super_effective': instance.notSuperEffective,
      'tips': instance.tips,
      'uncovered_types': instance.uncoveredTypes,
      'used_move_coverage': instance.usedMoveCoverage,
    };
