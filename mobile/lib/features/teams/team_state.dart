import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/misc.dart' show ProviderOrFamily;

import '../../api/export.dart';
import '../../data/server.dart';
import '../../data/teams_repository.dart';

final teamsRepositoryProvider = Provider<TeamsRepository>((ref) => TeamsRepository(ref.watch(dioProvider)));

final teamsListProvider = FutureProvider<List<TeamSummary>>((ref) => ref.watch(teamsRepositoryProvider).teams());
final teamProvider = FutureProvider.family<TeamOut, int>((ref, id) => ref.watch(teamsRepositoryProvider).team(id));

/// The analysis for (team, opponent?). The rating and profile live on the opponent-free one.
final teamAnalysisProvider = FutureProvider.family<TeamAnalysis, (int, int?)>(
  (ref, k) => ref.watch(teamsRepositoryProvider).analysis(k.$1, opponentId: k.$2),
);
final teamStrategyProvider = FutureProvider.family<TeamStrategy, int>((ref, id) => ref.watch(teamsRepositoryProvider).strategy(id));
final teamSummaryProvider = FutureProvider.family<TeamSummaryOut, int>((ref, id) => ref.watch(teamsRepositoryProvider).summary(id));

final naturesProvider = FutureProvider<List<NatureOut>>((ref) => ref.watch(teamsRepositoryProvider).natures());
final legalMovesProvider = FutureProvider.family<List<LearnsetMoveOut>, (int, int?)>(
  (ref, k) => ref.watch(teamsRepositoryProvider).legalMoves(k.$1, formId: k.$2),
);
final abilitiesProvider = FutureProvider.family<List<AbilityOut>, int>((ref, id) => ref.watch(teamsRepositoryProvider).abilities(id));

/// After any write to a team: everything derived from it is stale (list card, team,
/// analyses with any opponent, strategy, summary).
void invalidateTeam(Ref ref, int id) => _invalidate(ref.invalidate, id);
void invalidateTeamW(WidgetRef ref, int id) => _invalidate(ref.invalidate, id);

void _invalidate(void Function(ProviderOrFamily) inv, int id) {
  inv(teamsListProvider);
  inv(teamProvider(id));
  inv(teamAnalysisProvider);
  inv(teamStrategyProvider(id));
  inv(teamSummaryProvider(id));
}
