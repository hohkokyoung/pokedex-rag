// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'evolution_chip_tone.dart';

part 'evolution_chip.g.dart';

@JsonSerializable()
class EvolutionChip {
  const EvolutionChip({
    required this.label,
    required this.tone,
  });
  
  factory EvolutionChip.fromJson(Map<String, Object?> json) => _$EvolutionChipFromJson(json);
  
  final String label;
  final EvolutionChipTone tone;

  Map<String, Object?> toJson() => _$EvolutionChipToJson(this);
}
