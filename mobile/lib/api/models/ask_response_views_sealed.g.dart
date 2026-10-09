// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'ask_response_views_sealed.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

Map<String, dynamic> _$AskResponseViewsSealedToJson(
  AskResponseViewsSealed instance,
) => <String, dynamic>{};

AskResponseViewsSealedBuildProposalView
_$AskResponseViewsSealedBuildProposalViewFromJson(Map<String, dynamic> json) =>
    AskResponseViewsSealedBuildProposalView(
      build: BuildSuggestion.fromJson(json['build'] as Map<String, dynamic>),
      chunkRefs: (json['chunkRefs'] as List<dynamic>?)
          ?.map((e) => (e as num).toInt())
          .toList(),
      kind: json['kind'] as String,
      pokemon: json['pokemon'] as String,
      slot: (json['slot'] as num).toInt(),
      step: json['step'] as String?,
    );

Map<String, dynamic> _$AskResponseViewsSealedBuildProposalViewToJson(
  AskResponseViewsSealedBuildProposalView instance,
) => <String, dynamic>{
  'build': instance.build,
  'chunkRefs': instance.chunkRefs,
  'kind': instance.kind,
  'pokemon': instance.pokemon,
  'slot': instance.slot,
  'step': instance.step,
};

AskResponseViewsSealedCandidatesView
_$AskResponseViewsSealedCandidatesViewFromJson(Map<String, dynamic> json) =>
    AskResponseViewsSealedCandidatesView(
      candidates: (json['candidates'] as List<dynamic>)
          .map((e) => Candidate.fromJson(e as Map<String, dynamic>))
          .toList(),
      chunkRefs: (json['chunkRefs'] as List<dynamic>?)
          ?.map((e) => (e as num).toInt())
          .toList(),
      kind: json['kind'] as String,
      members: (json['members'] as List<dynamic>?)
          ?.map((e) => SlotRef.fromJson(e as Map<String, dynamic>))
          .toList(),
      step: json['step'] as String?,
      teamFull: json['teamFull'] as bool,
      teamId: (json['teamId'] as num).toInt(),
    );

Map<String, dynamic> _$AskResponseViewsSealedCandidatesViewToJson(
  AskResponseViewsSealedCandidatesView instance,
) => <String, dynamic>{
  'candidates': instance.candidates,
  'chunkRefs': instance.chunkRefs,
  'kind': instance.kind,
  'members': instance.members,
  'step': instance.step,
  'teamFull': instance.teamFull,
  'teamId': instance.teamId,
};

AskResponseViewsSealedDamageView _$AskResponseViewsSealedDamageViewFromJson(
  Map<String, dynamic> json,
) => AskResponseViewsSealedDamageView(
  apply: (json['apply'] as List<dynamic>?)
      ?.map((e) => CalcApply.fromJson(e as Map<String, dynamic>))
      .toList(),
  attacker: CalcRef.fromJson(json['attacker'] as Map<String, dynamic>),
  changes: json['changes'] as List<dynamic>?,
  chunkRefs: (json['chunkRefs'] as List<dynamic>?)
      ?.map((e) => (e as num).toInt())
      .toList(),
  current: HitRange.fromJson(json['current'] as Map<String, dynamic>),
  defender: CalcRef.fromJson(json['defender'] as Map<String, dynamic>),
  kind: json['kind'] as String,
  move: MoveRow.fromJson(json['move'] as Map<String, dynamic>),
  step: json['step'] as String?,
  whatif: json['whatif'] == null
      ? null
      : HitRange.fromJson(json['whatif'] as Map<String, dynamic>),
);

Map<String, dynamic> _$AskResponseViewsSealedDamageViewToJson(
  AskResponseViewsSealedDamageView instance,
) => <String, dynamic>{
  'apply': instance.apply,
  'attacker': instance.attacker,
  'changes': instance.changes,
  'chunkRefs': instance.chunkRefs,
  'current': instance.current,
  'defender': instance.defender,
  'kind': instance.kind,
  'move': instance.move,
  'step': instance.step,
  'whatif': instance.whatif,
};

AskResponseViewsSealedDuelView _$AskResponseViewsSealedDuelViewFromJson(
  Map<String, dynamic> json,
) => AskResponseViewsSealedDuelView(
  chunkRefs: (json['chunkRefs'] as List<dynamic>?)
      ?.map((e) => (e as num).toInt())
      .toList(),
  duel: DuelOut.fromJson(json['duel'] as Map<String, dynamic>),
  kind: json['kind'] as String,
  opponentId: (json['opponentId'] as num).toInt(),
  step: json['step'] as String?,
  teamId: (json['teamId'] as num).toInt(),
);

Map<String, dynamic> _$AskResponseViewsSealedDuelViewToJson(
  AskResponseViewsSealedDuelView instance,
) => <String, dynamic>{
  'chunkRefs': instance.chunkRefs,
  'duel': instance.duel,
  'kind': instance.kind,
  'opponentId': instance.opponentId,
  'step': instance.step,
  'teamId': instance.teamId,
};

AskResponseViewsSealedLearnCheckView
_$AskResponseViewsSealedLearnCheckViewFromJson(Map<String, dynamic> json) =>
    AskResponseViewsSealedLearnCheckView(
      absent: json['absent'] as bool,
      chunkRefs: (json['chunkRefs'] as List<dynamic>?)
          ?.map((e) => (e as num).toInt())
          .toList(),
      game: json['game'] as String?,
      how: json['how'] as String?,
      kind: json['kind'] as String,
      maxLevel: (json['maxLevel'] as num?)?.toInt(),
      method: json['method'] as String?,
      move: MoveRow.fromJson(json['move'] as Map<String, dynamic>),
      ok: json['ok'] as bool,
      pokemon: PokemonCard.fromJson(json['pokemon'] as Map<String, dynamic>),
      step: json['step'] as String?,
    );

Map<String, dynamic> _$AskResponseViewsSealedLearnCheckViewToJson(
  AskResponseViewsSealedLearnCheckView instance,
) => <String, dynamic>{
  'absent': instance.absent,
  'chunkRefs': instance.chunkRefs,
  'game': instance.game,
  'how': instance.how,
  'kind': instance.kind,
  'maxLevel': instance.maxLevel,
  'method': instance.method,
  'move': instance.move,
  'ok': instance.ok,
  'pokemon': instance.pokemon,
  'step': instance.step,
};

AskResponseViewsSealedLearnersView _$AskResponseViewsSealedLearnersViewFromJson(
  Map<String, dynamic> json,
) => AskResponseViewsSealedLearnersView(
  byMethod: (json['byMethod'] as Map<String, dynamic>?)?.map(
    (k, e) => MapEntry(k, (e as num).toInt()),
  ),
  chunkRefs: (json['chunkRefs'] as List<dynamic>?)
      ?.map((e) => (e as num).toInt())
      .toList(),
  game: json['game'] as String?,
  kind: json['kind'] as String,
  maxLevel: (json['maxLevel'] as num?)?.toInt(),
  method: json['method'] as String?,
  move: MoveRow.fromJson(json['move'] as Map<String, dynamic>),
  rows: (json['rows'] as List<dynamic>)
      .map((e) => PokemonCard.fromJson(e as Map<String, dynamic>))
      .toList(),
  scope: (json['scope'] as List<dynamic>?)?.map((e) => e as String).toList(),
  step: json['step'] as String?,
  total: (json['total'] as num).toInt(),
);

Map<String, dynamic> _$AskResponseViewsSealedLearnersViewToJson(
  AskResponseViewsSealedLearnersView instance,
) => <String, dynamic>{
  'byMethod': instance.byMethod,
  'chunkRefs': instance.chunkRefs,
  'game': instance.game,
  'kind': instance.kind,
  'maxLevel': instance.maxLevel,
  'method': instance.method,
  'move': instance.move,
  'rows': instance.rows,
  'scope': instance.scope,
  'step': instance.step,
  'total': instance.total,
};

AskResponseViewsSealedLearnsetView _$AskResponseViewsSealedLearnsetViewFromJson(
  Map<String, dynamic> json,
) => AskResponseViewsSealedLearnsetView(
  chunkRefs: (json['chunkRefs'] as List<dynamic>?)
      ?.map((e) => (e as num).toInt())
      .toList(),
  game: json['game'] as String?,
  groups: (json['groups'] as List<dynamic>)
      .map((e) => LearnGroup.fromJson(e as Map<String, dynamic>))
      .toList(),
  kind: json['kind'] as String,
  pokemon: PokemonCard.fromJson(json['pokemon'] as Map<String, dynamic>),
  step: json['step'] as String?,
);

Map<String, dynamic> _$AskResponseViewsSealedLearnsetViewToJson(
  AskResponseViewsSealedLearnsetView instance,
) => <String, dynamic>{
  'chunkRefs': instance.chunkRefs,
  'game': instance.game,
  'groups': instance.groups,
  'kind': instance.kind,
  'pokemon': instance.pokemon,
  'step': instance.step,
};

AskResponseViewsSealedMemberAddedView
_$AskResponseViewsSealedMemberAddedViewFromJson(Map<String, dynamic> json) =>
    AskResponseViewsSealedMemberAddedView(
      added: json['added'] as bool,
      card: PokemonCard.fromJson(json['card'] as Map<String, dynamic>),
      chunkRefs: (json['chunkRefs'] as List<dynamic>?)
          ?.map((e) => (e as num).toInt())
          .toList(),
      kind: json['kind'] as String,
      message: json['message'] as String,
      slot: (json['slot'] as num?)?.toInt(),
      step: json['step'] as String?,
      teamId: (json['teamId'] as num).toInt(),
    );

Map<String, dynamic> _$AskResponseViewsSealedMemberAddedViewToJson(
  AskResponseViewsSealedMemberAddedView instance,
) => <String, dynamic>{
  'added': instance.added,
  'card': instance.card,
  'chunkRefs': instance.chunkRefs,
  'kind': instance.kind,
  'message': instance.message,
  'slot': instance.slot,
  'step': instance.step,
  'teamId': instance.teamId,
};

AskResponseViewsSealedMoveListView _$AskResponseViewsSealedMoveListViewFromJson(
  Map<String, dynamic> json,
) => AskResponseViewsSealedMoveListView(
  chunkRefs: (json['chunkRefs'] as List<dynamic>?)
      ?.map((e) => (e as num).toInt())
      .toList(),
  kind: json['kind'] as String,
  moves: (json['moves'] as List<dynamic>)
      .map((e) => MoveRow.fromJson(e as Map<String, dynamic>))
      .toList(),
  step: json['step'] as String?,
);

Map<String, dynamic> _$AskResponseViewsSealedMoveListViewToJson(
  AskResponseViewsSealedMoveListView instance,
) => <String, dynamic>{
  'chunkRefs': instance.chunkRefs,
  'kind': instance.kind,
  'moves': instance.moves,
  'step': instance.step,
};

AskResponseViewsSealedPokemonListView
_$AskResponseViewsSealedPokemonListViewFromJson(Map<String, dynamic> json) =>
    AskResponseViewsSealedPokemonListView(
      cards: (json['cards'] as List<dynamic>)
          .map((e) => PokemonCard.fromJson(e as Map<String, dynamic>))
          .toList(),
      chunkRefs: (json['chunkRefs'] as List<dynamic>?)
          ?.map((e) => (e as num).toInt())
          .toList(),
      kind: json['kind'] as String,
      step: json['step'] as String?,
      title: json['title'] as String?,
    );

Map<String, dynamic> _$AskResponseViewsSealedPokemonListViewToJson(
  AskResponseViewsSealedPokemonListView instance,
) => <String, dynamic>{
  'cards': instance.cards,
  'chunkRefs': instance.chunkRefs,
  'kind': instance.kind,
  'step': instance.step,
  'title': instance.title,
};

AskResponseViewsSealedRankingView _$AskResponseViewsSealedRankingViewFromJson(
  Map<String, dynamic> json,
) => AskResponseViewsSealedRankingView(
  chunkRefs: (json['chunkRefs'] as List<dynamic>?)
      ?.map((e) => (e as num).toInt())
      .toList(),
  kind: json['kind'] as String,
  order: RankingViewOrder.fromJson(json['order'] as String),
  rows: (json['rows'] as List<dynamic>)
      .map((e) => RankingRow.fromJson(e as Map<String, dynamic>))
      .toList(),
  stat: json['stat'] as String,
  step: json['step'] as String?,
  total: (json['total'] as num).toInt(),
);

Map<String, dynamic> _$AskResponseViewsSealedRankingViewToJson(
  AskResponseViewsSealedRankingView instance,
) => <String, dynamic>{
  'chunkRefs': instance.chunkRefs,
  'kind': instance.kind,
  'order': _$RankingViewOrderEnumMap[instance.order]!,
  'rows': instance.rows,
  'stat': instance.stat,
  'step': instance.step,
  'total': instance.total,
};

const _$RankingViewOrderEnumMap = {
  RankingViewOrder.asc: 'asc',
  RankingViewOrder.desc: 'desc',
  RankingViewOrder.$unknown: r'$unknown',
};

AskResponseViewsSealedSetEditView _$AskResponseViewsSealedSetEditViewFromJson(
  Map<String, dynamic> json,
) => AskResponseViewsSealedSetEditView(
  after: BuildSet.fromJson(json['after'] as Map<String, dynamic>),
  before: BuildSet.fromJson(json['before'] as Map<String, dynamic>),
  chunkRefs: (json['chunkRefs'] as List<dynamic>?)
      ?.map((e) => (e as num).toInt())
      .toList(),
  fields: json['fields'],
  kind: json['kind'] as String,
  member: json['member'],
  name: json['name'] as String,
  side: SetEditViewSide.fromJson(json['side'] as String),
  slot: (json['slot'] as num).toInt(),
  spriteUrl: json['spriteUrl'] as String,
  step: json['step'] as String?,
  teamId: (json['teamId'] as num).toInt(),
  why: json['why'] as String,
);

Map<String, dynamic> _$AskResponseViewsSealedSetEditViewToJson(
  AskResponseViewsSealedSetEditView instance,
) => <String, dynamic>{
  'after': instance.after,
  'before': instance.before,
  'chunkRefs': instance.chunkRefs,
  'fields': instance.fields,
  'kind': instance.kind,
  'member': instance.member,
  'name': instance.name,
  'side': _$SetEditViewSideEnumMap[instance.side]!,
  'slot': instance.slot,
  'spriteUrl': instance.spriteUrl,
  'step': instance.step,
  'teamId': instance.teamId,
  'why': instance.why,
};

const _$SetEditViewSideEnumMap = {
  SetEditViewSide.ours: 'ours',
  SetEditViewSide.theirs: 'theirs',
  SetEditViewSide.$unknown: r'$unknown',
};

AskResponseViewsSealedSurviveView _$AskResponseViewsSealedSurviveViewFromJson(
  Map<String, dynamic> json,
) => AskResponseViewsSealedSurviveView(
  already: json['already'] as bool,
  apply: json['apply'] == null
      ? null
      : CalcApply.fromJson(json['apply'] as Map<String, dynamic>),
  attacker: CalcRef.fromJson(json['attacker'] as Map<String, dynamic>),
  chunkRefs: (json['chunkRefs'] as List<dynamic>?)
      ?.map((e) => (e as num).toInt())
      .toList(),
  current: HitRange.fromJson(json['current'] as Map<String, dynamic>),
  defender: CalcRef.fromJson(json['defender'] as Map<String, dynamic>),
  hpEv: (json['hpEv'] as num).toInt(),
  kind: json['kind'] as String,
  move: MoveRow.fromJson(json['move'] as Map<String, dynamic>),
  nature: json['nature'] as String,
  natureChanged: json['natureChanged'] as bool,
  range: HitRange.fromJson(json['range'] as Map<String, dynamic>),
  stat: SurviveViewStat.fromJson(json['stat'] as String),
  statEv: (json['statEv'] as num).toInt(),
  step: json['step'] as String?,
  survives: json['survives'] as bool,
);

Map<String, dynamic> _$AskResponseViewsSealedSurviveViewToJson(
  AskResponseViewsSealedSurviveView instance,
) => <String, dynamic>{
  'already': instance.already,
  'apply': instance.apply,
  'attacker': instance.attacker,
  'chunkRefs': instance.chunkRefs,
  'current': instance.current,
  'defender': instance.defender,
  'hpEv': instance.hpEv,
  'kind': instance.kind,
  'move': instance.move,
  'nature': instance.nature,
  'natureChanged': instance.natureChanged,
  'range': instance.range,
  'stat': _$SurviveViewStatEnumMap[instance.stat]!,
  'statEv': instance.statEv,
  'step': instance.step,
  'survives': instance.survives,
};

const _$SurviveViewStatEnumMap = {
  SurviveViewStat.def: 'def',
  SurviveViewStat.spd: 'spd',
  SurviveViewStat.$unknown: r'$unknown',
};

AskResponseViewsSealedTypeChartView
_$AskResponseViewsSealedTypeChartViewFromJson(
  Map<String, dynamic> json,
) => AskResponseViewsSealedTypeChartView(
  chunkRefs: (json['chunkRefs'] as List<dynamic>?)
      ?.map((e) => (e as num).toInt())
      .toList(),
  immune: (json['immune'] as List<dynamic>?)?.map((e) => e as String).toList(),
  kind: json['kind'] as String,
  resistHalf: (json['resistHalf'] as List<dynamic>?)
      ?.map((e) => e as String)
      .toList(),
  resistQuarter: (json['resistQuarter'] as List<dynamic>?)
      ?.map((e) => e as String)
      .toList(),
  step: json['step'] as String?,
  strongAgainst: (json['strongAgainst'] as List<dynamic>?)
      ?.map((e) => e as String)
      .toList(),
  types: (json['types'] as List<dynamic>).map((e) => e as String).toList(),
  weak2x: (json['weak2x'] as List<dynamic>?)?.map((e) => e as String).toList(),
  weak4x: (json['weak4x'] as List<dynamic>?)?.map((e) => e as String).toList(),
);

Map<String, dynamic> _$AskResponseViewsSealedTypeChartViewToJson(
  AskResponseViewsSealedTypeChartView instance,
) => <String, dynamic>{
  'chunkRefs': instance.chunkRefs,
  'immune': instance.immune,
  'kind': instance.kind,
  'resistHalf': instance.resistHalf,
  'resistQuarter': instance.resistQuarter,
  'step': instance.step,
  'strongAgainst': instance.strongAgainst,
  'types': instance.types,
  'weak2x': instance.weak2x,
  'weak4x': instance.weak4x,
};
