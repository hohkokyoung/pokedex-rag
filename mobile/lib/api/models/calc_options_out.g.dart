// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'calc_options_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CalcOptionsOut _$CalcOptionsOutFromJson(Map<String, dynamic> json) =>
    CalcOptionsOut(
      abilities: (json['abilities'] as List<dynamic>)
          .map((e) => CalcOptionOut.fromJson(e as Map<String, dynamic>))
          .toList(),
      items: (json['items'] as List<dynamic>)
          .map((e) => CalcOptionOut.fromJson(e as Map<String, dynamic>))
          .toList(),
      natures: (json['natures'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      terrains: (json['terrains'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      weathers: (json['weathers'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
    );

Map<String, dynamic> _$CalcOptionsOutToJson(CalcOptionsOut instance) =>
    <String, dynamic>{
      'abilities': instance.abilities,
      'items': instance.items,
      'natures': instance.natures,
      'terrains': instance.terrains,
      'weathers': instance.weathers,
    };
