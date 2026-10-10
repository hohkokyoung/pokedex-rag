import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/export.dart';
import '../../data/errors.dart';
import '../../theme/theme.dart';
import '../../theme/tokens.g.dart';
import '../../widgets/ui.dart';
import '../ask/answer_text.dart';
import '../ask/ask_cards.dart';
import '../ask/ask_parts.dart';
import '../ask/ask_state.dart';
import '../pokedex/detail_sections.dart' show Section;
import 'coach_cards.dart';
import 'coach_state.dart';
import 'team_state.dart';

/// The website's quick questions for this team (and opponent).
List<String> coachQuestions(TeamOut team, TeamOut? opponent) {
  final members = [...team.members]..sort((a, b) => a.slot.compareTo(b.slot));
  const draft = 'Draft the rest of my team: I like sweepers, non-legendary';
  final qs = [
    "What's my team's biggest weakness?",
    opponent != null ? 'How do I beat ${opponent.name}?' : 'Which type should I add for coverage?',
    members.isNotEmpty ? 'Give ${members.first.name} its best set' : draft,
    draft,
  ];
  return [for (final (i, q) in qs.indexed) if (qs.indexOf(q) == i) q].take(4).toList();
}

/// The team coach: quick questions, a question box and this visit's thread. Apply / Add
/// / Replace / Revert / Undo on its cards are the only things that save.
class CoachSection extends ConsumerStatefulWidget {
  const CoachSection({super.key, required this.team, this.opponentId});

  final TeamOut team;
  final int? opponentId;

  @override
  ConsumerState<CoachSection> createState() => _CoachSectionState();
}

class _CoachSectionState extends ConsumerState<CoachSection> {
  final _field = TextEditingController();

  @override
  void dispose() {
    _field.dispose();
    super.dispose();
  }

  void _ask(String q) {
    if (q.trim().isEmpty) return;
    _field.clear();
    FocusScope.of(context).unfocus();
    ref.read(coachProvider(widget.team.id).notifier).ask(q, opponentId: widget.opponentId);
  }

  @override
  Widget build(BuildContext context) {
    final team = widget.team;
    final opponent = widget.opponentId == null ? null : ref.watch(teamProvider(widget.opponentId!)).value;
    final turns = ref.watch(coachProvider(team.id));
    final busy = turns.any((t) => t.status == AskStatus.streaming);
    final disabled = team.members.isEmpty;
    return Section(
      title: 'Coach',
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(
          'Ask anything about ${team.name}${opponent != null ? ' or ${opponent.name}' : ''}. It can also change a '
          "Pokémon's set — say “give ${team.members.firstOrNull?.name ?? 'Garchomp'} a faster set” — and nothing is "
          'saved until you press Apply.',
          style: AppText.bodySmall.copyWith(color: Palette.inkDim),
        ),
        for (final (i, t) in turns.indexed) _Turn(key: Key('coach-turn-$i'), turn: t),
        const SizedBox(height: Space.sm),
        Wrap(spacing: 6, runSpacing: 6, children: [
          for (final q in coachQuestions(team, opponent))
            ActionChip(
              key: Key('coach-q-$q'),
              label: Text(q, overflow: TextOverflow.ellipsis),
              onPressed: disabled || busy ? null : () => _ask(q),
            ),
        ]),
        const SizedBox(height: Space.sm),
        TextField(
          key: const Key('coach-field'),
          controller: _field,
          enabled: !disabled,
          autocorrect: false,
          textInputAction: TextInputAction.send,
          onSubmitted: busy ? null : _ask,
          minLines: 1,
          maxLines: 3,
          decoration: InputDecoration(
            hintText: disabled ? 'Add a Pokémon first…' : 'Ask the coach, or tell it what to change…',
            suffixIcon: SendButton(
              key: const Key('coach-send'),
              busy: busy,
              onPressed: disabled ? null : () => _ask(_field.text),
            ),
          ),
        ),
      ]),
    );
  }
}

class _Turn extends StatelessWidget {
  const _Turn({super.key, required this.turn});

  final AskState turn;

  @override
  Widget build(BuildContext context) {
    final t = turn;
    void cite(int n) {
      final s = sourceOf(t, n);
      if (s != null) showSourceSheet(context, s);
    }

    final edits = t.views.whereType<SetEditView>().length;
    return Padding(
      padding: const EdgeInsets.only(top: Space.md),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: Space.sm, vertical: 6),
          decoration: BoxDecoration(color: Palette.insetGray, borderRadius: BorderRadius.circular(Radii.inset)),
          child: Text(t.question, style: AppText.bodySmall.copyWith(fontWeight: FontWeight.w600)),
        ),
        const SizedBox(height: Space.xs),
        if (t.answer.isEmpty && t.status == AskStatus.streaming)
          Text(runningLine(t), style: AppText.bodySmall.copyWith(color: Palette.mutedSlate))
        else if (t.answer.isNotEmpty)
          AnswerText(t.answer, onCite: cite),
        if (t.status == AskStatus.error && t.answer.isEmpty)
          Text(
            t.error is Unreachable
                ? "Can't reach the server at ${(t.error! as Unreachable).address}."
                : t.errorMessage ?? "The coach couldn't answer. Try again.",
            key: const Key('coach-error'),
            style: AppText.bodySmall.copyWith(color: Palette.pokeballRedText),
          ),
        HowAnswered(run: t),
        if (edits > 1)
          Padding(
            padding: const EdgeInsets.only(top: Space.sm),
            child: Text('Suggested changes: apply the ones you want', style: AppText.label.copyWith(color: Palette.mutedSlate)),
          ),
        for (final v in t.views)
          switch (v) {
            SetEditView() => SetEditCard(view: v),
            CandidatesView() => CandidateCards(view: v),
            MemberAddedView() => MemberAddedStrip(view: v),
            DuelView() => DuelCard(view: v),
            _ => Padding(
                padding: const EdgeInsets.only(top: Space.sm),
                child: ViewCard(view: v, sources: t.sources, onCite: cite),
              ),
          },
      ]),
    );
  }
}
