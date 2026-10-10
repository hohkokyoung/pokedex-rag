// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'calc_proposal.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CalcProposal _$CalcProposalFromJson(Map<String, dynamic> json) => CalcProposal(
  build: BuildSuggestion.fromJson(json['build'] as Map<String, dynamic>),
  slot: (json['slot'] as num).toInt(),
  thread: (json['thread'] as List<dynamic>?)
      ?.map((e) => CoachTurn.fromJson(e as Map<String, dynamic>))
      .toList(),
);

Map<String, dynamic> _$CalcProposalToJson(CalcProposal instance) =>
    <String, dynamic>{
      'build': instance.build,
      'slot': instance.slot,
      'thread': instance.thread,
    };
