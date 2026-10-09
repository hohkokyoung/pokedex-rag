// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'member_defense.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MemberDefense _$MemberDefenseFromJson(Map<String, dynamic> json) =>
    MemberDefense(
      multipliers: Map<String, num>.from(json['multipliers'] as Map),
      name: json['name'] as String,
      slot: (json['slot'] as num).toInt(),
      types: (json['types'] as List<dynamic>).map((e) => e as String).toList(),
      weakTo: (json['weak_to'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
    );

Map<String, dynamic> _$MemberDefenseToJson(MemberDefense instance) =>
    <String, dynamic>{
      'multipliers': instance.multipliers,
      'name': instance.name,
      'slot': instance.slot,
      'types': instance.types,
      'weak_to': instance.weakTo,
    };
