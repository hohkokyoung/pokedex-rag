// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'flavor_entry.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

FlavorEntry _$FlavorEntryFromJson(Map<String, dynamic> json) => FlavorEntry(
  text: json['text'] as String,
  generations:
      (json['generations'] as List<dynamic>?)
          ?.map((e) => (e as num).toInt())
          .toList() ??
      const [],
  versionGenerations:
      (json['version_generations'] as List<dynamic>?)
          ?.map((e) => (e as num?)?.toInt())
          .toList() ??
      const [],
  versions:
      (json['versions'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
  generation: (json['generation'] as num?)?.toInt(),
  generationLabel: json['generation_label'] as String?,
  version: json['version'] as String?,
);

Map<String, dynamic> _$FlavorEntryToJson(FlavorEntry instance) =>
    <String, dynamic>{
      'generation': instance.generation,
      'generation_label': instance.generationLabel,
      'generations': instance.generations,
      'text': instance.text,
      'version': instance.version,
      'version_generations': instance.versionGenerations,
      'versions': instance.versions,
    };
