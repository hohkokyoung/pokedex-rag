// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'evolution_chip.dart';

part 'evolution_display.g.dart';

/// How a client labels one evolution step (services/evolution_display.py).
@JsonSerializable()
class EvolutionDisplay {
  const EvolutionDisplay({
    required this.chips,
    required this.description,
  });
  
  factory EvolutionDisplay.fromJson(Map<String, Object?> json) => _$EvolutionDisplayFromJson(json);
  
  final List<EvolutionChip> chips;
  final String? description;

  Map<String, Object?> toJson() => _$EvolutionDisplayToJson(this);
}
