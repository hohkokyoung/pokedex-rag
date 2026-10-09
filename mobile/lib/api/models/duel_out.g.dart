// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'duel_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

DuelOut _$DuelOutFromJson(Map<String, dynamic> json) => DuelOut(
  first: DuelOutFirst.fromJson(json['first'] as String),
  ourName: json['our_name'] as String,
  ourSlot: (json['our_slot'] as num).toInt(),
  outcome: DuelOutOutcome.fromJson(json['outcome'] as String),
  theirName: json['their_name'] as String,
  theirSlot: (json['their_slot'] as num).toInt(),
  ourSetup: json['our_setup'] as String?,
  theirSetup: json['their_setup'] as String?,
  log:
      (json['log'] as List<dynamic>?)
          ?.map((e) => DuelEvent.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  notes:
      (json['notes'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
  ourMoves:
      (json['our_moves'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
  ourMovesLearned:
      (json['our_moves_learned'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  theirMoves:
      (json['their_moves'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  theirMovesLearned:
      (json['their_moves_learned'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
);

Map<String, dynamic> _$DuelOutToJson(DuelOut instance) => <String, dynamic>{
  'first': _$DuelOutFirstEnumMap[instance.first]!,
  'log': instance.log,
  'notes': instance.notes,
  'our_moves': instance.ourMoves,
  'our_moves_learned': instance.ourMovesLearned,
  'our_name': instance.ourName,
  'our_setup': instance.ourSetup,
  'our_slot': instance.ourSlot,
  'outcome': _$DuelOutOutcomeEnumMap[instance.outcome]!,
  'their_moves': instance.theirMoves,
  'their_moves_learned': instance.theirMovesLearned,
  'their_name': instance.theirName,
  'their_setup': instance.theirSetup,
  'their_slot': instance.theirSlot,
};

const _$DuelOutFirstEnumMap = {
  DuelOutFirst.ours: 'ours',
  DuelOutFirst.theirs: 'theirs',
  DuelOutFirst.tie: 'tie',
  DuelOutFirst.$unknown: r'$unknown',
};

const _$DuelOutOutcomeEnumMap = {
  DuelOutOutcome.win: 'win',
  DuelOutOutcome.lose: 'lose',
  DuelOutOutcome.even: 'even',
  DuelOutOutcome.$unknown: r'$unknown',
};
