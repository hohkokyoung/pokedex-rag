// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'evolution_display.dart';

part 'evolution_stage.g.dart';

@JsonSerializable()
class EvolutionStage {
  const EvolutionStage({
    required this.toId,
    required this.toName,
    this.condition,
    this.display,
    this.fromId,
    this.fromName,
    this.item,
    this.minLevel,
    this.trigger,
  });
  
  factory EvolutionStage.fromJson(Map<String, Object?> json) => _$EvolutionStageFromJson(json);
  
  final String? condition;
  final EvolutionDisplay? display;
  @JsonKey(name: 'from_id')
  final int? fromId;
  @JsonKey(name: 'from_name')
  final String? fromName;
  final String? item;
  @JsonKey(name: 'min_level')
  final int? minLevel;
  @JsonKey(name: 'to_id')
  final int toId;
  @JsonKey(name: 'to_name')
  final String toName;
  final String? trigger;

  Map<String, Object?> toJson() => _$EvolutionStageToJson(this);
}
