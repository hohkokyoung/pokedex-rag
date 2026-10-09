// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'evolution_chip.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

EvolutionChip _$EvolutionChipFromJson(Map<String, dynamic> json) =>
    EvolutionChip(
      label: json['label'] as String,
      tone: EvolutionChipTone.fromJson(json['tone'] as String),
    );

Map<String, dynamic> _$EvolutionChipToJson(EvolutionChip instance) =>
    <String, dynamic>{
      'label': instance.label,
      'tone': _$EvolutionChipToneEnumMap[instance.tone]!,
    };

const _$EvolutionChipToneEnumMap = {
  EvolutionChipTone.solid: 'solid',
  EvolutionChipTone.soft: 'soft',
  EvolutionChipTone.$unknown: r'$unknown',
};
