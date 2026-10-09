// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'candidates_view.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CandidatesView _$CandidatesViewFromJson(Map<String, dynamic> json) =>
    CandidatesView(
      candidates: (json['candidates'] as List<dynamic>)
          .map((e) => Candidate.fromJson(e as Map<String, dynamic>))
          .toList(),
      teamId: (json['team_id'] as num).toInt(),
      kind: json['kind'] as String? ?? 'candidates',
      teamFull: json['team_full'] as bool? ?? false,
      chunkRefs: (json['chunk_refs'] as List<dynamic>?)
          ?.map((e) => (e as num).toInt())
          .toList(),
      members: (json['members'] as List<dynamic>?)
          ?.map((e) => SlotRef.fromJson(e as Map<String, dynamic>))
          .toList(),
      step: json['step'] as String?,
    );

Map<String, dynamic> _$CandidatesViewToJson(CandidatesView instance) =>
    <String, dynamic>{
      'candidates': instance.candidates,
      'chunk_refs': instance.chunkRefs,
      'kind': instance.kind,
      'members': instance.members,
      'step': instance.step,
      'team_full': instance.teamFull,
      'team_id': instance.teamId,
    };
