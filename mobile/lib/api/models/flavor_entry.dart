// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'flavor_entry.g.dart';

/// A dex entry plus the game(s) and generation(s) it comes from.
@JsonSerializable()
class FlavorEntry {
  const FlavorEntry({
    required this.text,
    this.generations = const [],
    this.versionGenerations = const [],
    this.versions = const [],
    this.generation,
    this.generationLabel,
    this.version,
  });
  
  factory FlavorEntry.fromJson(Map<String, Object?> json) => _$FlavorEntryFromJson(json);
  
  final int? generation;
  @JsonKey(name: 'generation_label')
  final String? generationLabel;
  final List<int> generations;
  final String text;
  final String? version;
  @JsonKey(name: 'version_generations')
  final List<int?> versionGenerations;
  final List<String> versions;

  Map<String, Object?> toJson() => _$FlavorEntryToJson(this);
}
