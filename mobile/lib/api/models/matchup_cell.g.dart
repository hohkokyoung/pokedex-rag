// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'matchup_cell.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MatchupCell _$MatchupCellFromJson(Map<String, dynamic> json) => MatchupCell(
  faster: MatchupCellFaster.fromJson(json['faster'] as String),
  ourHit: json['our_hit'] as num,
  ourSlot: (json['our_slot'] as num).toInt(),
  outcome: MatchupCellOutcome.fromJson(json['outcome'] as String),
  score: json['score'] as num,
  theirHit: json['their_hit'] as num,
  theirSlot: (json['their_slot'] as num).toInt(),
  ourHitType: json['our_hit_type'] as String?,
  ourMove: json['our_move'] as String?,
  ourSetup: json['our_setup'] as String?,
  theirHitType: json['their_hit_type'] as String?,
  theirMove: json['their_move'] as String?,
  theirSetup: json['their_setup'] as String?,
  notes:
      (json['notes'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
  ourHko: (json['our_hko'] as num?)?.toInt() ?? 99,
  ourMoveLearned: json['our_move_learned'] as bool? ?? false,
  ourPct: json['our_pct'] as num? ?? 0,
  theirHko: (json['their_hko'] as num?)?.toInt() ?? 99,
  theirMoveLearned: json['their_move_learned'] as bool? ?? false,
  theirPct: json['their_pct'] as num? ?? 0,
);

Map<String, dynamic> _$MatchupCellToJson(MatchupCell instance) =>
    <String, dynamic>{
      'faster': _$MatchupCellFasterEnumMap[instance.faster]!,
      'notes': instance.notes,
      'our_hit': instance.ourHit,
      'our_hit_type': instance.ourHitType,
      'our_hko': instance.ourHko,
      'our_move': instance.ourMove,
      'our_move_learned': instance.ourMoveLearned,
      'our_pct': instance.ourPct,
      'our_setup': instance.ourSetup,
      'our_slot': instance.ourSlot,
      'outcome': _$MatchupCellOutcomeEnumMap[instance.outcome]!,
      'score': instance.score,
      'their_hit': instance.theirHit,
      'their_hit_type': instance.theirHitType,
      'their_hko': instance.theirHko,
      'their_move': instance.theirMove,
      'their_move_learned': instance.theirMoveLearned,
      'their_pct': instance.theirPct,
      'their_setup': instance.theirSetup,
      'their_slot': instance.theirSlot,
    };

const _$MatchupCellFasterEnumMap = {
  MatchupCellFaster.ours: 'ours',
  MatchupCellFaster.theirs: 'theirs',
  MatchupCellFaster.tie: 'tie',
  MatchupCellFaster.$unknown: r'$unknown',
};

const _$MatchupCellOutcomeEnumMap = {
  MatchupCellOutcome.win: 'win',
  MatchupCellOutcome.lose: 'lose',
  MatchupCellOutcome.even: 'even',
  MatchupCellOutcome.$unknown: r'$unknown',
};
