// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'evolution_display.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

EvolutionDisplay _$EvolutionDisplayFromJson(Map<String, dynamic> json) =>
    EvolutionDisplay(
      chips: (json['chips'] as List<dynamic>)
          .map((e) => EvolutionChip.fromJson(e as Map<String, dynamic>))
          .toList(),
      description: json['description'] as String?,
    );

Map<String, dynamic> _$EvolutionDisplayToJson(EvolutionDisplay instance) =>
    <String, dynamic>{
      'chips': instance.chips,
      'description': instance.description,
    };
