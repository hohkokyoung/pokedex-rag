// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'encounter_game_out.g.dart';

@JsonSerializable()
class EncounterGameOut {
  const EncounterGameOut({
    required this.generation,
    required this.places,
    required this.version,
    required this.versionId,
  });
  
  factory EncounterGameOut.fromJson(Map<String, Object?> json) => _$EncounterGameOutFromJson(json);
  
  final int generation;
  final int places;
  final String version;
  @JsonKey(name: 'version_id')
  final int versionId;

  Map<String, Object?> toJson() => _$EncounterGameOutToJson(this);
}
