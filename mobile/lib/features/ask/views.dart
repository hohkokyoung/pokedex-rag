import '../../api/export.dart';

/// Decodes one Ask view with the generated per-kind class for its `kind`.
///
/// (swagger_parser's sealed union, AskResponseViewsSealed, drops the snake_case JSON
/// keys on its subclasses, so fields like `chunk_refs` and `weak_2x` would decode as
/// null. The per-kind classes map them correctly.) Returns null for a kind this app
/// doesn't draw, so the rest of the answer still shows.
Object? decodeView(Map<String, dynamic> json) => switch (json['kind']) {
      'ranking' => RankingView.fromJson(json),
      'pokemon_list' => PokemonListView.fromJson(json),
      'type_chart' => TypeChartView.fromJson(json),
      'move_list' => MoveListView.fromJson(json),
      'learnset' => LearnsetView.fromJson(json),
      'learners' => LearnersView.fromJson(json),
      'learn_check' => LearnCheckView.fromJson(json),
      // The team coach's own cards.
      'set_edit' => SetEditView.fromJson(json),
      'candidates' => CandidatesView.fromJson(json),
      'member_added' => MemberAddedView.fromJson(json),
      'duel' => DuelView.fromJson(json),
      // The calculator coach's.
      'damage' => DamageView.fromJson(json),
      'survive' => SurviveView.fromJson(json),
      'build_proposal' => BuildProposalView.fromJson(json),
      _ => null,
    };
