// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'build_proposal_view.dart';
import 'build_set.dart';
import 'build_suggestion.dart';
import 'calc_apply.dart';
import 'calc_ref.dart';
import 'candidate.dart';
import 'candidates_view.dart';
import 'damage_view.dart';
import 'duel_out.dart';
import 'duel_view.dart';
import 'hit_range.dart';
import 'learn_check_view.dart';
import 'learn_group.dart';
import 'learners_view.dart';
import 'learnset_view.dart';
import 'member_added_view.dart';
import 'move_list_view.dart';
import 'move_row.dart';
import 'pokemon_card.dart';
import 'pokemon_list_view.dart';
import 'ranking_row.dart';
import 'ranking_view.dart';
import 'ranking_view_order.dart';
import 'set_edit_view.dart';
import 'set_edit_view_side.dart';
import 'slot_ref.dart';
import 'survive_view.dart';
import 'survive_view_stat.dart';
import 'type_chart_view.dart';


part 'ask_response_views_sealed.g.dart';

@JsonSerializable(createFactory: false)
sealed class AskResponseViewsSealed {
  const AskResponseViewsSealed();
  
  factory AskResponseViewsSealed.fromJson(Map<String, dynamic> json) =>
      AskResponseViewsSealedDeserializer.tryDeserialize(json);
  
  Map<String, dynamic> toJson();
}

extension AskResponseViewsSealedDeserializer on AskResponseViewsSealed {
  static AskResponseViewsSealed tryDeserialize(
    Map<String, dynamic> json, {
    String key = 'kind',
    Map<Type, Object?>? mapping,
  }) {
    final mappingFallback = const <Type, Object?>{
      AskResponseViewsSealedBuildProposalView: 'build_proposal',
      AskResponseViewsSealedCandidatesView: 'candidates',
      AskResponseViewsSealedDamageView: 'damage',
      AskResponseViewsSealedDuelView: 'duel',
      AskResponseViewsSealedLearnCheckView: 'learn_check',
      AskResponseViewsSealedLearnersView: 'learners',
      AskResponseViewsSealedLearnsetView: 'learnset',
      AskResponseViewsSealedMemberAddedView: 'member_added',
      AskResponseViewsSealedMoveListView: 'move_list',
      AskResponseViewsSealedPokemonListView: 'pokemon_list',
      AskResponseViewsSealedRankingView: 'ranking',
      AskResponseViewsSealedSetEditView: 'set_edit',
      AskResponseViewsSealedSurviveView: 'survive',
      AskResponseViewsSealedTypeChartView: 'type_chart',
    };
    final value = json[key];
    final effective = mapping ?? mappingFallback;
    return switch (value) {
      _ when value == effective[AskResponseViewsSealedBuildProposalView] => AskResponseViewsSealedBuildProposalView.fromJson(json),
      _ when value == effective[AskResponseViewsSealedCandidatesView] => AskResponseViewsSealedCandidatesView.fromJson(json),
      _ when value == effective[AskResponseViewsSealedDamageView] => AskResponseViewsSealedDamageView.fromJson(json),
      _ when value == effective[AskResponseViewsSealedDuelView] => AskResponseViewsSealedDuelView.fromJson(json),
      _ when value == effective[AskResponseViewsSealedLearnCheckView] => AskResponseViewsSealedLearnCheckView.fromJson(json),
      _ when value == effective[AskResponseViewsSealedLearnersView] => AskResponseViewsSealedLearnersView.fromJson(json),
      _ when value == effective[AskResponseViewsSealedLearnsetView] => AskResponseViewsSealedLearnsetView.fromJson(json),
      _ when value == effective[AskResponseViewsSealedMemberAddedView] => AskResponseViewsSealedMemberAddedView.fromJson(json),
      _ when value == effective[AskResponseViewsSealedMoveListView] => AskResponseViewsSealedMoveListView.fromJson(json),
      _ when value == effective[AskResponseViewsSealedPokemonListView] => AskResponseViewsSealedPokemonListView.fromJson(json),
      _ when value == effective[AskResponseViewsSealedRankingView] => AskResponseViewsSealedRankingView.fromJson(json),
      _ when value == effective[AskResponseViewsSealedSetEditView] => AskResponseViewsSealedSetEditView.fromJson(json),
      _ when value == effective[AskResponseViewsSealedSurviveView] => AskResponseViewsSealedSurviveView.fromJson(json),
      _ when value == effective[AskResponseViewsSealedTypeChartView] => AskResponseViewsSealedTypeChartView.fromJson(json),
      _ => throw FormatException('Unknown discriminator value "${json[key]}" for AskResponseViewsSealed'),
    };
  }
}

@JsonSerializable()
class AskResponseViewsSealedBuildProposalView extends AskResponseViewsSealed implements BuildProposalView {
  @override
  final BuildSuggestion build;
  @override
  final List<int>? chunkRefs;
  @override
  final String kind;
  @override
  final String pokemon;
  @override
  final int slot;
  @override
  final String? step;

  const AskResponseViewsSealedBuildProposalView({
    required this.build,
    required this.chunkRefs,
    required this.kind,
    required this.pokemon,
    required this.slot,
    required this.step,
  });
  
  factory AskResponseViewsSealedBuildProposalView.fromJson(Map<String, dynamic> json) =>
      _$AskResponseViewsSealedBuildProposalViewFromJson(json);
      
  @override
  Map<String, dynamic> toJson() => _$AskResponseViewsSealedBuildProposalViewToJson(this);
}
@JsonSerializable()
class AskResponseViewsSealedCandidatesView extends AskResponseViewsSealed implements CandidatesView {
  @override
  final List<Candidate> candidates;
  @override
  final List<int>? chunkRefs;
  @override
  final String kind;
  @override
  final List<SlotRef>? members;
  @override
  final String? step;
  @override
  final bool teamFull;
  @override
  final int teamId;

  const AskResponseViewsSealedCandidatesView({
    required this.candidates,
    required this.chunkRefs,
    required this.kind,
    required this.members,
    required this.step,
    required this.teamFull,
    required this.teamId,
  });
  
  factory AskResponseViewsSealedCandidatesView.fromJson(Map<String, dynamic> json) =>
      _$AskResponseViewsSealedCandidatesViewFromJson(json);
      
  @override
  Map<String, dynamic> toJson() => _$AskResponseViewsSealedCandidatesViewToJson(this);
}
@JsonSerializable()
class AskResponseViewsSealedDamageView extends AskResponseViewsSealed implements DamageView {
  @override
  final List<CalcApply>? apply;
  @override
  final CalcRef attacker;
  @override
  final List<dynamic>? changes;
  @override
  final List<int>? chunkRefs;
  @override
  final HitRange current;
  @override
  final CalcRef defender;
  @override
  final String kind;
  @override
  final MoveRow move;
  @override
  final String? step;
  @override
  final HitRange? whatif;

  const AskResponseViewsSealedDamageView({
    required this.apply,
    required this.attacker,
    required this.changes,
    required this.chunkRefs,
    required this.current,
    required this.defender,
    required this.kind,
    required this.move,
    required this.step,
    required this.whatif,
  });
  
  factory AskResponseViewsSealedDamageView.fromJson(Map<String, dynamic> json) =>
      _$AskResponseViewsSealedDamageViewFromJson(json);
      
  @override
  Map<String, dynamic> toJson() => _$AskResponseViewsSealedDamageViewToJson(this);
}
@JsonSerializable()
class AskResponseViewsSealedDuelView extends AskResponseViewsSealed implements DuelView {
  @override
  final List<int>? chunkRefs;
  @override
  final DuelOut duel;
  @override
  final String kind;
  @override
  final int opponentId;
  @override
  final String? step;
  @override
  final int teamId;

  const AskResponseViewsSealedDuelView({
    required this.chunkRefs,
    required this.duel,
    required this.kind,
    required this.opponentId,
    required this.step,
    required this.teamId,
  });
  
  factory AskResponseViewsSealedDuelView.fromJson(Map<String, dynamic> json) =>
      _$AskResponseViewsSealedDuelViewFromJson(json);
      
  @override
  Map<String, dynamic> toJson() => _$AskResponseViewsSealedDuelViewToJson(this);
}
@JsonSerializable()
class AskResponseViewsSealedLearnCheckView extends AskResponseViewsSealed implements LearnCheckView {
  @override
  final bool absent;
  @override
  final List<int>? chunkRefs;
  @override
  final String? game;
  @override
  final String? how;
  @override
  final String kind;
  @override
  final int? maxLevel;
  @override
  final String? method;
  @override
  final MoveRow move;
  @override
  final bool ok;
  @override
  final PokemonCard pokemon;
  @override
  final String? step;

  const AskResponseViewsSealedLearnCheckView({
    required this.absent,
    required this.chunkRefs,
    required this.game,
    required this.how,
    required this.kind,
    required this.maxLevel,
    required this.method,
    required this.move,
    required this.ok,
    required this.pokemon,
    required this.step,
  });
  
  factory AskResponseViewsSealedLearnCheckView.fromJson(Map<String, dynamic> json) =>
      _$AskResponseViewsSealedLearnCheckViewFromJson(json);
      
  @override
  Map<String, dynamic> toJson() => _$AskResponseViewsSealedLearnCheckViewToJson(this);
}
@JsonSerializable()
class AskResponseViewsSealedLearnersView extends AskResponseViewsSealed implements LearnersView {
  @override
  final Map<String, int>? byMethod;
  @override
  final List<int>? chunkRefs;
  @override
  final String? game;
  @override
  final String kind;
  @override
  final int? maxLevel;
  @override
  final String? method;
  @override
  final MoveRow move;
  @override
  final List<PokemonCard> rows;
  @override
  final List<String>? scope;
  @override
  final String? step;
  @override
  final int total;

  const AskResponseViewsSealedLearnersView({
    required this.byMethod,
    required this.chunkRefs,
    required this.game,
    required this.kind,
    required this.maxLevel,
    required this.method,
    required this.move,
    required this.rows,
    required this.scope,
    required this.step,
    required this.total,
  });
  
  factory AskResponseViewsSealedLearnersView.fromJson(Map<String, dynamic> json) =>
      _$AskResponseViewsSealedLearnersViewFromJson(json);
      
  @override
  Map<String, dynamic> toJson() => _$AskResponseViewsSealedLearnersViewToJson(this);
}
@JsonSerializable()
class AskResponseViewsSealedLearnsetView extends AskResponseViewsSealed implements LearnsetView {
  @override
  final List<int>? chunkRefs;
  @override
  final String? game;
  @override
  final List<LearnGroup> groups;
  @override
  final String kind;
  @override
  final PokemonCard pokemon;
  @override
  final String? step;

  const AskResponseViewsSealedLearnsetView({
    required this.chunkRefs,
    required this.game,
    required this.groups,
    required this.kind,
    required this.pokemon,
    required this.step,
  });
  
  factory AskResponseViewsSealedLearnsetView.fromJson(Map<String, dynamic> json) =>
      _$AskResponseViewsSealedLearnsetViewFromJson(json);
      
  @override
  Map<String, dynamic> toJson() => _$AskResponseViewsSealedLearnsetViewToJson(this);
}
@JsonSerializable()
class AskResponseViewsSealedMemberAddedView extends AskResponseViewsSealed implements MemberAddedView {
  @override
  final bool added;
  @override
  final PokemonCard card;
  @override
  final List<int>? chunkRefs;
  @override
  final String kind;
  @override
  final String message;
  @override
  final int? slot;
  @override
  final String? step;
  @override
  final int teamId;

  const AskResponseViewsSealedMemberAddedView({
    required this.added,
    required this.card,
    required this.chunkRefs,
    required this.kind,
    required this.message,
    required this.slot,
    required this.step,
    required this.teamId,
  });
  
  factory AskResponseViewsSealedMemberAddedView.fromJson(Map<String, dynamic> json) =>
      _$AskResponseViewsSealedMemberAddedViewFromJson(json);
      
  @override
  Map<String, dynamic> toJson() => _$AskResponseViewsSealedMemberAddedViewToJson(this);
}
@JsonSerializable()
class AskResponseViewsSealedMoveListView extends AskResponseViewsSealed implements MoveListView {
  @override
  final List<int>? chunkRefs;
  @override
  final String kind;
  @override
  final List<MoveRow> moves;
  @override
  final String? step;

  const AskResponseViewsSealedMoveListView({
    required this.chunkRefs,
    required this.kind,
    required this.moves,
    required this.step,
  });
  
  factory AskResponseViewsSealedMoveListView.fromJson(Map<String, dynamic> json) =>
      _$AskResponseViewsSealedMoveListViewFromJson(json);
      
  @override
  Map<String, dynamic> toJson() => _$AskResponseViewsSealedMoveListViewToJson(this);
}
@JsonSerializable()
class AskResponseViewsSealedPokemonListView extends AskResponseViewsSealed implements PokemonListView {
  @override
  final List<PokemonCard> cards;
  @override
  final List<int>? chunkRefs;
  @override
  final String kind;
  @override
  final String? step;
  @override
  final String? title;

  const AskResponseViewsSealedPokemonListView({
    required this.cards,
    required this.chunkRefs,
    required this.kind,
    required this.step,
    required this.title,
  });
  
  factory AskResponseViewsSealedPokemonListView.fromJson(Map<String, dynamic> json) =>
      _$AskResponseViewsSealedPokemonListViewFromJson(json);
      
  @override
  Map<String, dynamic> toJson() => _$AskResponseViewsSealedPokemonListViewToJson(this);
}
@JsonSerializable()
class AskResponseViewsSealedRankingView extends AskResponseViewsSealed implements RankingView {
  @override
  final List<int>? chunkRefs;
  @override
  final String kind;
  @override
  final RankingViewOrder order;
  @override
  final List<RankingRow> rows;
  @override
  final String stat;
  @override
  final String? step;
  @override
  final int total;

  const AskResponseViewsSealedRankingView({
    required this.chunkRefs,
    required this.kind,
    required this.order,
    required this.rows,
    required this.stat,
    required this.step,
    required this.total,
  });
  
  factory AskResponseViewsSealedRankingView.fromJson(Map<String, dynamic> json) =>
      _$AskResponseViewsSealedRankingViewFromJson(json);
      
  @override
  Map<String, dynamic> toJson() => _$AskResponseViewsSealedRankingViewToJson(this);
}
@JsonSerializable()
class AskResponseViewsSealedSetEditView extends AskResponseViewsSealed implements SetEditView {
  @override
  final BuildSet after;
  @override
  final BuildSet before;
  @override
  final List<int>? chunkRefs;
  @override
  final dynamic fields;
  @override
  final String kind;
  @override
  final dynamic member;
  @override
  final String name;
  @override
  final SetEditViewSide side;
  @override
  final int slot;
  @override
  final String spriteUrl;
  @override
  final String? step;
  @override
  final int teamId;
  @override
  final String why;

  const AskResponseViewsSealedSetEditView({
    required this.after,
    required this.before,
    required this.chunkRefs,
    required this.fields,
    required this.kind,
    required this.member,
    required this.name,
    required this.side,
    required this.slot,
    required this.spriteUrl,
    required this.step,
    required this.teamId,
    required this.why,
  });
  
  factory AskResponseViewsSealedSetEditView.fromJson(Map<String, dynamic> json) =>
      _$AskResponseViewsSealedSetEditViewFromJson(json);
      
  @override
  Map<String, dynamic> toJson() => _$AskResponseViewsSealedSetEditViewToJson(this);
}
@JsonSerializable()
class AskResponseViewsSealedSurviveView extends AskResponseViewsSealed implements SurviveView {
  @override
  final bool already;
  @override
  final CalcApply? apply;
  @override
  final CalcRef attacker;
  @override
  final List<int>? chunkRefs;
  @override
  final HitRange current;
  @override
  final CalcRef defender;
  @override
  final int hpEv;
  @override
  final String kind;
  @override
  final MoveRow move;
  @override
  final String nature;
  @override
  final bool natureChanged;
  @override
  final HitRange range;
  @override
  final SurviveViewStat stat;
  @override
  final int statEv;
  @override
  final String? step;
  @override
  final bool survives;

  const AskResponseViewsSealedSurviveView({
    required this.already,
    required this.apply,
    required this.attacker,
    required this.chunkRefs,
    required this.current,
    required this.defender,
    required this.hpEv,
    required this.kind,
    required this.move,
    required this.nature,
    required this.natureChanged,
    required this.range,
    required this.stat,
    required this.statEv,
    required this.step,
    required this.survives,
  });
  
  factory AskResponseViewsSealedSurviveView.fromJson(Map<String, dynamic> json) =>
      _$AskResponseViewsSealedSurviveViewFromJson(json);
      
  @override
  Map<String, dynamic> toJson() => _$AskResponseViewsSealedSurviveViewToJson(this);
}
@JsonSerializable()
class AskResponseViewsSealedTypeChartView extends AskResponseViewsSealed implements TypeChartView {
  @override
  final List<int>? chunkRefs;
  @override
  final List<String>? immune;
  @override
  final String kind;
  @override
  final List<String>? resistHalf;
  @override
  final List<String>? resistQuarter;
  @override
  final String? step;
  @override
  final List<String>? strongAgainst;
  @override
  final List<String> types;
  @override
  final List<String>? weak2x;
  @override
  final List<String>? weak4x;

  const AskResponseViewsSealedTypeChartView({
    required this.chunkRefs,
    required this.immune,
    required this.kind,
    required this.resistHalf,
    required this.resistQuarter,
    required this.step,
    required this.strongAgainst,
    required this.types,
    required this.weak2x,
    required this.weak4x,
  });
  
  factory AskResponseViewsSealedTypeChartView.fromJson(Map<String, dynamic> json) =>
      _$AskResponseViewsSealedTypeChartViewFromJson(json);
      
  @override
  Map<String, dynamic> toJson() => _$AskResponseViewsSealedTypeChartViewToJson(this);
}
