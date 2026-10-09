// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'defensive_profile.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

DefensiveProfile _$DefensiveProfileFromJson(Map<String, dynamic> json) =>
    DefensiveProfile(
      matrix: (json['matrix'] as List<dynamic>)
          .map((e) => MemberDefense.fromJson(e as Map<String, dynamic>))
          .toList(),
      sharedWeaknesses: (json['shared_weaknesses'] as List<dynamic>)
          .map((e) => SharedWeakness.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$DefensiveProfileToJson(DefensiveProfile instance) =>
    <String, dynamic>{
      'matrix': instance.matrix,
      'shared_weaknesses': instance.sharedWeaknesses,
    };
