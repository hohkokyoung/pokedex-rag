import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/export.dart';
import '../../data/server.dart';
import '../ask/ask_state.dart';
import 'team_state.dart';

/// The coach thread for one team while its page is open (the website keeps none either).
/// Each turn is an Ask-shaped run streamed from /api/teams/{id}/ask.
final coachProvider = NotifierProvider.autoDispose.family<Coach, List<AskState>, int>(Coach.new);

class Coach extends Notifier<List<AskState>> {
  Coach(this.teamId);

  final int teamId;
  CancelToken? _cancel;

  @override
  List<AskState> build() {
    ref.onDispose(() => _cancel?.cancel());
    return const [];
  }

  bool get busy => state.any((t) => t.status == AskStatus.streaming);

  /// Asks one question (ignored while another is streaming, as on the website).
  Future<void> ask(String question, {int? opponentId}) async {
    final q = question.trim();
    if (q.isEmpty || busy) return;
    final i = state.length;
    final cancel = _cancel = CancelToken();
    state = [...state, AskState(question: q, status: AskStatus.streaming)];
    await streamAsk(
      ref.read(dioProvider),
      '/api/teams/$teamId/ask',
      CoachAskRequest(question: q, opponentId: opponentId).toJson(),
      cancel,
      read: () => state[i],
      emit: (turn) => state = [...state.sublist(0, i), turn, ...state.sublist(i + 1)],
      onOther: (e) {
        // The coach added a member for an explicit "add X": refetch the page.
        if (e.name == 'team_updated') invalidateTeam(ref, teamId);
      },
    );
  }
}

/// A member exactly as saved, for Revert / Undo-replace (the website's restoreMember).
SlotUpdate restoreUpdate(TeamMemberOut m) => SlotUpdate(
      pokemonId: m.pokemonId,
      formId: m.formId,
      abilityId: m.ability?.id,
      natureId: m.nature?.id,
      itemId: m.item?.id,
      evSpread: m.evSpread,
      ivSpread: m.ivSpread,
      moveIds: m.moves.isEmpty ? null : [for (final x in m.moves) x.moveId],
    );

/// The first empty slot (1–6), or null on a full team.
int? firstEmptySlot(TeamOut team) {
  final taken = {for (final m in team.members) m.slot};
  for (var s = 1; s <= 6; s++) {
    if (!taken.contains(s)) return s;
  }
  return null;
}
