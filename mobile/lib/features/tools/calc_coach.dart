import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/export.dart';
import '../../data/server.dart';
import '../ask/ask_state.dart';
import 'calc_state.dart';

/// The website's one-tap starters, and its follow-ups once a build is on the table.
const coachStart = ['Best build', 'Bulky set', 'Fast sweeper'];
const coachQuick = ['Make it bulkier', 'Make it faster', 'No Choice item', 'Try a special set', 'Explain the EVs'];

/// The calculator coach's conversation about one slot, and the build it proposed there.
/// `prev` is the slot before the first Apply (what Revert restores); `applied` says the
/// current proposal is in.
class CalcCoach {
  const CalcCoach({required this.slot, required this.mon, this.turns = const [], this.build, this.pick, this.prev, this.applied = false});

  final int slot;
  final CalcPick mon;
  final List<AskState> turns;
  final BuildSuggestion? build;
  final String? pick; // the moveset chip picked to apply with
  final CalcSet? prev;
  final bool applied;

  bool get busy => turns.any((t) => t.status == AskStatus.streaming);

  CalcCoach copyWith({int? slot, CalcPick? mon, List<AskState>? turns, BuildSuggestion? build, String? pick, CalcSet? prev,
          bool? applied, bool clearPick = false, bool clearPrev = false}) =>
      CalcCoach(
        slot: slot ?? this.slot,
        mon: mon ?? this.mon,
        turns: turns ?? this.turns,
        build: build ?? this.build,
        pick: clearPick ? null : pick ?? this.pick,
        prev: clearPrev ? null : prev ?? this.prev,
        applied: applied ?? this.applied,
      );
}

/// The coach plus the damage / survive cards applied into the calculator: card key → the
/// slots as they were, for Revert.
class CoachModel {
  const CoachModel({this.coach, this.cardPrev = const {}});

  final CalcCoach? coach;
  final Map<String, Map<int, CalcSet>> cardPrev;
}

/// Same build, ignoring the reasoning (the website's sameBuild).
bool sameBuild(BuildSuggestion a, BuildSuggestion? b) =>
    b != null && a.ability == b.ability && a.nature == b.nature && a.item == b.item && _eq(a.moves, b.moves) && _eqm(a.evs, b.evs);
bool _eq(List<String> a, List<String> b) => a.length == b.length && [for (var i = 0; i < a.length; i++) a[i] == b[i]].every((x) => x);
bool _eqm(Map<String, int> a, Map<String, int> b) => a.length == b.length && a.entries.every((e) => b[e.key] == e.value);

final calcCoachProvider = NotifierProvider<CalcCoachNotifier, CoachModel>(CalcCoachNotifier.new);

class CalcCoachNotifier extends Notifier<CoachModel> {
  CancelToken? _cancel;
  int _seq = 0;

  @override
  CoachModel build() {
    ref.onDispose(() => _cancel?.cancel());
    return const CoachModel();
  }

  CalcModel get _calc => ref.read(calcProvider);

  /// The coach for the focused slot, while it still holds the same Pokémon.
  CalcCoach? coachFor(int slot) {
    final c = state.coach;
    return c != null && c.slot == slot && _calc.sets[slot].mon == c.mon ? c : null;
  }

  void _setCoach(CalcCoach? c) => state = CoachModel(coach: c, cardPrev: state.cardPrev);

  /// One question → one streamed turn, with the calculator as it is now. [hits] are the
  /// server turn's hits the calculator shows.
  Future<void> ask(String question, int focus, List<CalcHitOut> hits) async {
    final q = question.trim();
    final mon = _calc.sets[focus].mon;
    if (q.isEmpty || mon == null || (coachFor(focus)?.busy ?? false)) return;
    final cur = coachFor(focus);
    final c = cur ?? CalcCoach(slot: focus, mon: mon);
    final idx = c.turns.length;
    final id = ++_seq;
    final req = _calc.request();
    final body = CalcAskRequest(
      question: q,
      level: req.level,
      doubles: req.doubles,
      field: req.field,
      slots: req.slots,
      focus: focus,
      hits: [
        for (final h in hits)
          CalcHitIn(attacker: h.attacker, target: h.target, move: h.move, minPct: h.minPct, maxPct: h.maxPct, ko: h.koHits, te: h.te),
      ],
      proposal: c.build == null
          ? null
          : CalcProposal(slot: c.slot, build: c.build!, thread: [
              for (final t in c.turns.where((t) => t.status == AskStatus.done)) CoachTurn(ask: t.question, reply: t.answer),
            ]),
    );
    _setCoach(c.copyWith(turns: [...c.turns, AskState(question: q, status: AskStatus.streaming)]));
    _cancel?.cancel();
    final cancel = _cancel = CancelToken();
    bool mine() => _seq == id && state.coach != null;
    await streamAsk(
      ref.read(dioProvider),
      '/api/calc/ask',
      body.toJson(),
      cancel,
      read: () => state.coach!.turns[idx],
      emit: (t) {
        if (!mine()) return;
        final cc = state.coach!;
        _setCoach(cc.copyWith(turns: [...cc.turns.sublist(0, idx), t, ...cc.turns.sublist(idx + 1)]));
        final b = t.views.whereType<BuildProposalView>().lastOrNull;
        if (b != null) _takeBuild(b);
      },
    );
  }

  /// A proposal becomes the build card: a new set goes back to pending; a reply that leaves
  /// it alone keeps it applied; a build for another slot moves the coach there.
  void _takeBuild(BuildProposalView v) {
    final c = state.coach!;
    if (sameBuild(v.build, c.build) && v.slot == c.slot) return;
    final mon = _calc.sets[v.slot].mon;
    if (mon == null) return;
    if (v.slot != c.slot || mon != c.mon) {
      _setCoach(c.copyWith(slot: v.slot, mon: mon, build: v.build, applied: false, clearPick: true, clearPrev: true));
    } else {
      _setCoach(c.copyWith(build: v.build, applied: false, clearPick: true));
    }
  }

  void pickMove(String name) {
    final c = state.coach;
    if (c == null) return;
    if (c.applied) {
      ref.read(calcProvider.notifier).update(c.slot, (s) => s.copyWith(move: name));
    } else {
      _setCoach(c.copyWith(pick: name));
    }
  }

  /// The move Apply uses: the picked chip, else the build's first damaging move, else its first.
  String? applyMove(List<LearnsetMoveOut> learnset) {
    final c = state.coach;
    if (c?.build == null) return null;
    LearnsetMoveOut? at(String n) => learnset.where((m) => m.name == n).firstOrNull;
    if (c!.pick != null && at(c.pick!) != null) return c.pick;
    final names = c.build!.moves;
    return names.where((n) => (at(n)?.power ?? 0) > 0).firstOrNull ?? names.where((n) => at(n) != null).firstOrNull;
  }

  void applyBuild(List<LearnsetMoveOut> learnset) {
    final c = state.coach;
    if (c?.build == null || _calc.sets[c!.slot].mon != c.mon) return;
    final b = c.build!;
    final cur = _calc.sets[c.slot];
    final move = applyMove(learnset);
    _setCoach(c.copyWith(prev: c.prev ?? cur, applied: true));
    ref.read(calcProvider.notifier).update(
          c.slot,
          (s) => s.copyWith(
            ability: b.ability ?? s.ability,
            nature: b.nature ?? s.nature,
            item: b.item ?? s.item,
            ev: {for (final k in statKeys) k: b.evs[k] ?? 0},
            pre: 'Custom',
            move: move ?? s.move,
          ),
        );
  }

  void revertBuild() {
    final c = state.coach;
    if (c?.prev == null) return;
    ref.read(calcProvider.notifier).update(c!.slot, (_) => c.prev!);
    _setCoach(c.copyWith(applied: false, clearPrev: true));
  }

  /// Apply a damage / survive card's fields into the calculator (never a saved team).
  void applyCard(String key, List<CalcApply> applies) {
    final before = <int, CalcSet>{};
    final calc = ref.read(calcProvider.notifier);
    for (final a in applies) {
      final cur = _calc.sets[a.slot];
      if (cur.mon == null) continue;
      before[a.slot] = cur;
      final p = Map<String, dynamic>.from(a.fields as Map);
      calc.update(a.slot, (s) => s.copyWith(
            item: p['item'] as String?,
            ability: p['ability'] as String?,
            nature: p['nature'] as String?,
            ev: p['evs'] is Map ? {...s.ev, for (final e in (p['evs'] as Map).entries) '${e.key}': (e.value as num).toInt()} : null,
            hp: (p['hp'] as num?)?.toInt(),
            pre: 'Custom',
          ));
    }
    state = CoachModel(coach: state.coach, cardPrev: {...state.cardPrev, key: before});
  }

  void revertCard(String key) {
    final before = state.cardPrev[key];
    if (before == null) return;
    final calc = ref.read(calcProvider.notifier);
    for (final MapEntry(key: slot, value: set) in before.entries) {
      calc.update(slot, (_) => set);
    }
    state = CoachModel(coach: state.coach, cardPrev: {...state.cardPrev}..remove(key));
  }
}

