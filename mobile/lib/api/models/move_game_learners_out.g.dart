// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'move_game_learners_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MoveGameLearnersOut _$MoveGameLearnersOutFromJson(Map<String, dynamic> json) =>
    MoveGameLearnersOut(
      games: (json['games'] as List<dynamic>)
          .map((e) => GameOut.fromJson(e as Map<String, dynamic>))
          .toList(),
      learners: (json['learners'] as List<dynamic>)
          .map((e) => GameLearnerOut.fromJson(e as Map<String, dynamic>))
          .toList(),
      moveId: (json['move_id'] as num).toInt(),
      total: (json['total'] as num).toInt(),
      versionGroupId: (json['version_group_id'] as num?)?.toInt(),
      lastMachine: json['last_machine'] as String?,
      lastMachineGame: json['last_machine_game'] as String?,
      machine: json['machine'] as String?,
    );

Map<String, dynamic> _$MoveGameLearnersOutToJson(
  MoveGameLearnersOut instance,
) => <String, dynamic>{
  'games': instance.games,
  'last_machine': instance.lastMachine,
  'last_machine_game': instance.lastMachineGame,
  'learners': instance.learners,
  'machine': instance.machine,
  'move_id': instance.moveId,
  'total': instance.total,
  'version_group_id': instance.versionGroupId,
};
