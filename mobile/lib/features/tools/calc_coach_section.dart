import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/export.dart';
import '../../data/errors.dart';
import '../../theme/theme.dart';
import '../../theme/tokens.g.dart';
import '../ask/answer_text.dart';
import '../ask/ask_cards.dart' show ViewCard;
import '../ask/ask_parts.dart';
import '../ask/ask_state.dart';
import '../pokedex/detail_sections.dart' show Section;
import 'calc_coach.dart';
import 'calc_state.dart';

String _pct(HitRange r) => '${r.minPct.toStringAsFixed(1)}–${r.maxPct.toStringAsFixed(1)}%';
String _ko(HitRange r) => r.koText.isNotEmpty ? r.koText : (r.ko == 0 ? 'no damage' : '${r.ko}HKO');

/// The calculator's coach for the focused Pokémon: quick questions, the box, the
/// conversation, and cards that apply into the calculator only on a click.
class CalcCoachSection extends ConsumerStatefulWidget {
  const CalcCoachSection({super.key, required this.focus, required this.turn});

  final int focus;
  final CalcTurnOut? turn;

  @override
  ConsumerState<CalcCoachSection> createState() => _CalcCoachSectionState();
}

class _CalcCoachSectionState extends ConsumerState<CalcCoachSection> {
  final _field = TextEditingController();

  @override
  void dispose() {
    _field.dispose();
    super.dispose();
  }

  List<CalcHitOut> get _hits => widget.turn?.steps.expand((s) => s.hits).toList() ?? const [];

  void _ask(String q) {
    if (q.trim().isEmpty) return;
    _field.clear();
    FocusScope.of(context).unfocus();
    ref.read(calcCoachProvider.notifier).ask(q, widget.focus, _hits);
  }

  @override
  Widget build(BuildContext context) {
    ref.watch(calcCoachProvider);
    final m = ref.watch(calcProvider);
    final n = ref.read(calcCoachProvider.notifier);
    final f = widget.focus;
    final s = m.sets[f];
    if (s.mon == null) return const SizedBox.shrink();
    final c = n.coachFor(f);
    final busy = c?.busy ?? false;
    // Damage questions about the focused matchup, answered by the calculator itself (no LLM).
    final foe = widget.turn?.aims['$f'];
    final foeSet = foe == null ? null : m.sets[foe];
    final calcChips = [
      if (foeSet?.mon != null && (s.move != null)) 'Can ${s.mon!.name} OHKO ${foeSet!.mon!.name}?',
      if (foeSet?.mon != null && foeSet!.move != null)
        "How much bulk does ${s.mon!.name} need to survive ${foeSet.mon!.name}'s ${foeSet.move}?",
    ];
    return Section(
      title: 'Coach',
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        if (c?.build != null)
          _BuildCard(coach: c!, set: m.sets[c.slot])
        else
          Text.rich(TextSpan(style: AppText.bodySmall.copyWith(color: Palette.inkDim), children: [
            const TextSpan(text: 'Ask the coach about '),
            TextSpan(text: s.mon!.name, style: const TextStyle(fontWeight: FontWeight.w700)),
            const TextSpan(text: '. Damage and bulk questions are answered by the calculator itself.'),
          ])),
        for (final (j, t) in (c?.turns ?? const <AskState>[]).indexed) _Turn(key: Key('calc-turn-$j'), turn: t, cardKey: '${c!.slot}:$j'),
        const SizedBox(height: Space.sm),
        Wrap(spacing: 6, runSpacing: 6, children: [
          for (final q in [...(c?.build != null ? coachQuick : coachStart), ...calcChips])
            ActionChip(key: Key('calc-q-$q'), label: Text(q, overflow: TextOverflow.ellipsis), onPressed: busy ? null : () => _ask(q)),
        ]),
        const SizedBox(height: Space.sm),
        TextField(
          key: const Key('calc-coach-field'),
          controller: _field,
          autocorrect: false,
          enabled: !busy,
          textInputAction: TextInputAction.send,
          onSubmitted: _ask,
          minLines: 1,
          maxLines: 3,
          decoration: InputDecoration(
            hintText: c?.build != null
                ? 'Ask a follow-up, e.g. "swap ${c!.build!.moves.lastOrNull ?? 'a move'} for a priority move"'
                : 'What should ${s.mon!.name} do? e.g. "a bulky set for doubles"',
            suffixIcon: IconButton(
              key: const Key('calc-coach-send'),
              icon: busy
                  ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.arrow_upward),
              onPressed: busy ? null : () => _ask(_field.text),
            ),
          ),
        ),
      ]),
    );
  }
}

class _Turn extends ConsumerWidget {
  const _Turn({super.key, required this.turn, required this.cardKey});

  final AskState turn;
  final String cardKey;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = turn;
    final model = ref.watch(calcCoachProvider);
    final calc = ref.watch(calcProvider);
    final n = ref.read(calcCoachProvider.notifier);
    bool live(CalcRef r) => calc.sets[r.slot].mon?.name == r.name;
    // No sources list here, so the [n] markers would point nowhere (as on the website).
    final answer = t.answer.replaceAll(RegExp(r' ?\[\d+(?:,\s*\d+)*\]'), '');
    return Padding(
      padding: const EdgeInsets.only(top: Space.md),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: Space.sm, vertical: 6),
          decoration: BoxDecoration(color: Palette.insetGray, borderRadius: BorderRadius.circular(Radii.inset)),
          child: Text(t.question, style: AppText.bodySmall.copyWith(fontWeight: FontWeight.w600)),
        ),
        const SizedBox(height: Space.xs),
        if (answer.isEmpty && t.status == AskStatus.streaming)
          Text('Coach is thinking…', style: AppText.bodySmall.copyWith(color: Palette.mutedSlate))
        else if (answer.isNotEmpty)
          AnswerText(answer, onCite: (_) {}),
        if (t.status == AskStatus.error && t.answer.isEmpty)
          Text(
            t.error is Unreachable ? "Can't reach the server at ${(t.error! as Unreachable).address}." : t.errorMessage ?? "The coach couldn't answer.",
            key: const Key('calc-coach-error'),
            style: AppText.bodySmall.copyWith(color: Palette.pokeballRedText),
          ),
        HowAnswered(run: t),
        for (final (k, v) in t.views.indexed)
          switch (v) {
            DamageView() => _DamageCard(
                key: Key('damage-card-$k'),
                view: v,
                live: live(v.attacker) && live(v.defender),
                applied: model.cardPrev.containsKey('$cardKey:$k'),
                onApply: () => n.applyCard('$cardKey:$k', v.apply ?? const []),
                onRevert: () => n.revertCard('$cardKey:$k'),
              ),
            SurviveView() => _SurviveCard(
                key: Key('survive-card-$k'),
                view: v,
                live: live(v.defender),
                applied: model.cardPrev.containsKey('$cardKey:$k'),
                onApply: () => v.apply == null ? null : n.applyCard('$cardKey:$k', [v.apply!]),
                onRevert: () => n.revertCard('$cardKey:$k'),
              ),
            BuildProposalView() => const SizedBox.shrink(), // drawn as the build card above
            _ => Padding(padding: const EdgeInsets.only(top: Space.sm), child: ViewCard(view: v, sources: t.sources, onCite: (_) {})),
          },
      ]),
    );
  }
}

class _Card extends StatelessWidget {
  const _Card({required this.title, required this.rows, this.action});

  final InlineSpan title;
  final List<Widget> rows;
  final Widget? action;

  @override
  Widget build(BuildContext context) => Container(
        margin: const EdgeInsets.only(top: Space.sm),
        padding: const EdgeInsets.all(Space.sm),
        decoration: BoxDecoration(
          color: Palette.panelWhite,
          borderRadius: BorderRadius.circular(Radii.inset),
          border: Border.all(color: Palette.hairline),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Expanded(child: Text.rich(TextSpan(style: AppText.bodySmall, children: [title]))),
            ?action,
          ]),
          ...rows,
        ]),
      );
}

Widget _row(String k, String v, {String? tag, Color? tone}) => Padding(
      padding: const EdgeInsets.only(top: 4),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        SizedBox(width: 96, child: Text(k, style: AppText.bodySmall.copyWith(color: Palette.mutedSlate))),
        // Value and tag wrap together: a long tag ("takes 34–40% — can't survive") fits a phone.
        Expanded(
          child: Wrap(spacing: Space.sm, children: [
            Text(v, style: AppText.readout.copyWith(fontSize: 12.5, fontWeight: FontWeight.w700)),
            if (tag != null) Text(tag, style: AppText.bodySmall.copyWith(color: tone ?? Palette.inkDim)),
          ]),
        ),
      ]),
    );

Widget _actions(String label, String key, {required bool live, required bool applied, required VoidCallback onApply, required VoidCallback onRevert}) =>
    applied
        ? OutlinedButton(key: Key('$key-revert'), onPressed: onRevert, child: const Text('Revert'))
        : FilledButton(key: Key('$key-apply'), onPressed: live ? onApply : null, child: Text(label));

/// "Can X OHKO Y?": the calculator's hit, plus the what-if when the question changed something.
class _DamageCard extends StatelessWidget {
  const _DamageCard({super.key, required this.view, required this.live, required this.applied, required this.onApply, required this.onRevert});

  final DamageView view;
  final bool live;
  final bool applied;
  final VoidCallback onApply;
  final VoidCallback onRevert;

  @override
  Widget build(BuildContext context) {
    final v = view;
    final changed = [for (final c in v.changes ?? const []) '${(c as Map)['value']}'].join(', ');
    return _Card(
      title: TextSpan(children: [
        TextSpan(text: v.attacker.name, style: const TextStyle(fontWeight: FontWeight.w700)),
        TextSpan(text: '’s ${v.move.name} → '),
        TextSpan(text: v.defender.name, style: const TextStyle(fontWeight: FontWeight.w700)),
      ]),
      action: v.whatif != null && (v.apply ?? const []).isNotEmpty
          ? _actions('Apply', 'damage', live: live, applied: applied, onApply: onApply, onRevert: onRevert)
          : null,
      rows: [
        _row(v.whatif != null ? 'Now' : 'Damage', _pct(v.current), tag: _ko(v.current)),
        if (v.whatif != null) _row('With $changed', _pct(v.whatif!), tag: _ko(v.whatif!)),
      ],
    );
  }
}

/// "How much bulk to survive?": the smallest spread that lives, and what the hit then does.
class _SurviveCard extends StatelessWidget {
  const _SurviveCard({super.key, required this.view, required this.live, required this.applied, required this.onApply, required this.onRevert});

  final SurviveView view;
  final bool live;
  final bool applied;
  final VoidCallback onApply;
  final VoidCallback onRevert;

  @override
  Widget build(BuildContext context) {
    final v = view;
    final stat = v.stat == SurviveViewStat.def ? 'Def' : 'SpD';
    final spread = [if (v.hpEv > 0) '${v.hpEv} HP', if (v.statEv > 0) '${v.statEv} $stat'].join(' / ');
    return _Card(
      title: TextSpan(children: [
        TextSpan(text: v.defender.name, style: const TextStyle(fontWeight: FontWeight.w700)),
        TextSpan(text: ' vs ${v.attacker.name}’s ${v.move.name}'),
      ]),
      action: v.apply != null ? _actions('Apply EVs', 'survive', live: live, applied: applied, onApply: onApply, onRevert: onRevert) : null,
      rows: [
        _row('Now', _pct(v.current), tag: _ko(v.current)),
        if (v.already)
          _row('Verdict', 'Already survives as set', tone: Palette.verdictGreenText)
        else
          _row(
            v.survives ? 'Survives with' : 'Best try',
            '${spread.isEmpty ? 'no EVs' : spread}${v.natureChanged ? ' · ${v.nature}' : ''}',
            tag: 'takes ${_pct(v.range)}${v.survives ? '' : ' — can’t survive'}',
            tone: v.survives ? Palette.verdictGreenText : Palette.pokeballRedText,
          ),
      ],
    );
  }
}

/// The proposed build against the calculator's current set, its moveset, Apply / Revert.
class _BuildCard extends ConsumerWidget {
  const _BuildCard({required this.coach, required this.set});

  final CalcCoach coach;
  final CalcSet set;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final b = coach.build!;
    final n = ref.read(calcCoachProvider.notifier);
    final learnset = ref.watch(calcMovesProvider(coach.mon)).value ?? const <LearnsetMoveOut>[];
    final base = coach.applied && coach.prev != null ? coach.prev! : set;
    final pick = coach.applied ? set.move : n.applyMove(learnset);
    String ev(Map<String, int> e) => [for (final k in statKeys) if ((e[k] ?? 0) > 0) '${e[k]} ${statShort[k]}'].join(' / ').ifBlank('none');
    final rows = [
      ('Ability', base.ability, b.ability),
      ('Nature', base.nature, b.nature),
      ('Item', base.item == 'None' ? 'No item' : base.item, b.item),
      ('EVs', ev(base.ev), ev(b.evs)),
    ];
    return Container(
      key: const Key('build-card'),
      padding: const EdgeInsets.all(Space.sm),
      decoration: BoxDecoration(
        color: Palette.panelWhite,
        borderRadius: BorderRadius.circular(Radii.inset),
        border: Border.all(color: coach.applied ? Palette.verdictGreen : Palette.hairline),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Expanded(
            child: Text.rich(TextSpan(style: AppText.bodySmall, children: [
              TextSpan(text: coach.applied ? 'Applied to ' : 'Proposed build for '),
              TextSpan(text: coach.mon.name, style: const TextStyle(fontWeight: FontWeight.w700)),
            ])),
          ),
          if (coach.applied)
            OutlinedButton(key: const Key('build-revert'), onPressed: n.revertBuild, child: const Text('Revert'))
          else
            FilledButton(key: const Key('build-apply'), onPressed: () => n.applyBuild(learnset), child: const Text('Apply')),
        ]),
        for (final (k, was, now) in rows)
          Padding(
            padding: const EdgeInsets.only(top: 3),
            child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              SizedBox(width: 64, child: Text(k, style: AppText.bodySmall.copyWith(color: Palette.mutedSlate))),
              Expanded(
                child: now == null || now == was
                    ? Text(was, style: AppText.bodySmall)
                    : Text.rich(TextSpan(style: AppText.bodySmall, children: [
                        TextSpan(text: was, style: const TextStyle(decoration: TextDecoration.lineThrough, color: Palette.mutedSlate)),
                        const TextSpan(text: '  →  '),
                        TextSpan(text: now, style: const TextStyle(fontWeight: FontWeight.w700)),
                      ])),
              ),
            ]),
          ),
        const SizedBox(height: Space.xs),
        Text('Full moveset', style: AppText.label.copyWith(color: Palette.mutedSlate)),
        Wrap(spacing: 6, runSpacing: 4, children: [
          for (final name in b.moves)
            () {
              final mv = learnset.where((x) => x.name == name).firstOrNull;
              return ChoiceChip(
                key: Key('build-move-$name'),
                avatar: mv?.type == null ? null : CircleAvatar(backgroundColor: TypeColors.fill[mv!.type!] ?? Palette.mutedSlate, radius: 5),
                label: Text(name),
                selected: pick == name,
                onSelected: mv == null ? null : (_) => n.pickMove(name),
              );
            }(),
        ]),
        if (b.why.isNotEmpty) Padding(padding: const EdgeInsets.only(top: Space.xs), child: Text(b.why, style: AppText.bodySmall.copyWith(color: Palette.inkDim))),
      ]),
    );
  }
}

extension on String {
  String ifBlank(String other) => isEmpty ? other : this;
}
