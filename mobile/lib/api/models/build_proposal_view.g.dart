// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'build_proposal_view.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

BuildProposalView _$BuildProposalViewFromJson(Map<String, dynamic> json) =>
    BuildProposalView(
      build: BuildSuggestion.fromJson(json['build'] as Map<String, dynamic>),
      pokemon: json['pokemon'] as String,
      slot: (json['slot'] as num).toInt(),
      kind: json['kind'] as String? ?? 'build_proposal',
      chunkRefs: (json['chunk_refs'] as List<dynamic>?)
          ?.map((e) => (e as num).toInt())
          .toList(),
      step: json['step'] as String?,
    );

Map<String, dynamic> _$BuildProposalViewToJson(BuildProposalView instance) =>
    <String, dynamic>{
      'build': instance.build,
      'chunk_refs': instance.chunkRefs,
      'kind': instance.kind,
      'pokemon': instance.pokemon,
      'slot': instance.slot,
      'step': instance.step,
    };
