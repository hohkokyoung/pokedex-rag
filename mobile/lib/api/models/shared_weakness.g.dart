// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'shared_weakness.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SharedWeakness _$SharedWeaknessFromJson(Map<String, dynamic> json) =>
    SharedWeakness(
      count: (json['count'] as num).toInt(),
      members: (json['members'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      type: json['type'] as String,
    );

Map<String, dynamic> _$SharedWeaknessToJson(SharedWeakness instance) =>
    <String, dynamic>{
      'count': instance.count,
      'members': instance.members,
      'type': instance.type,
    };
