import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/export.dart';
import '../../theme/theme.dart';
import '../../theme/tokens.g.dart';
import '../../widgets/grade.dart';
import '../../widgets/type_chip.dart';
import '../../widgets/ui.dart' show Spinner;
import '../pokedex/detail_more.dart' show SectionError;
import '../pokedex/detail_sections.dart' show Section;
import 'team_state.dart';

/// The team page's report, built only from server fields: rating and profile on the
/// opponent-free analysis, strategy axes, the stored summary, sets and suggestions.
class TeamReport extends ConsumerWidget {
  const TeamReport({super.key, required this.team});

  final TeamOut team;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final a = ref.watch(teamAnalysisProvider((team.id, null)));
    return switch (a) {
      AsyncData(:final value) when value.rating != null => Column(
        children: [
          _RatingCard(team: team, a: value),
          const SizedBox(height: Space.md),
          _GradesCard(rating: value.rating!),
          const SizedBox(height: Space.md),
          _HowItPlays(teamId: team.id),
          const SizedBox(height: Space.md),
          _TypeProfile(p: value.profile!),
          const SizedBox(height: Space.md),
          _SetsCard(team: team, a: value),
          const SizedBox(height: Space.md),
          _DefenceCard(rating: value.rating!, a: value),
        ],
      ),
      AsyncData() => const SizedBox.shrink(),
      AsyncError(:final error) => SectionError(
        error: error,
        onRetry: () => ref.invalidate(teamAnalysisProvider((team.id, null))),
      ),
      _ => const Padding(padding: EdgeInsets.all(Space.lg), child: LinearProgressIndicator(minHeight: 2)),
    };
  }
}

// ---------------------------------------------------------------- rating + summary

class _RatingCard extends ConsumerStatefulWidget {
  const _RatingCard({required this.team, required this.a});

  final TeamOut team;
  final TeamAnalysis a;

  @override
  ConsumerState<_RatingCard> createState() => _RatingCardState();
}

class _RatingCardState extends ConsumerState<_RatingCard> {
  int _rechecks = 0;
  Timer? _timer;
  bool _regenerating = false;

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final r = widget.a.rating!;
    final summary = ref.watch(teamSummaryProvider(widget.team.id));
    // A rewrite in progress: look again a couple of times, never poll forever.
    final pending = summary.value?.pending ?? false;
    if (pending && _rechecks < 2 && !(_timer?.isActive ?? false)) {
      _timer = Timer(const Duration(seconds: 4), () {
        _rechecks++;
        if (mounted) ref.invalidate(teamSummaryProvider(widget.team.id));
      });
    }
    // The grade and rating line are the page header (team_screen's _Header); this is the summary.
    return Section(
      title: 'Summary',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (r.capped)
            Padding(
              padding: const EdgeInsets.only(bottom: Space.xs),
              child: Text(
                'Overall scaled to ${r.ceiling}/100 until the team has six different Pokémon.',
                style: AppText.bodySmall.copyWith(color: Palette.mutedSlate),
              ),
            ),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                margin: const EdgeInsets.only(top: 2, right: 6),
                padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                decoration: BoxDecoration(color: Palette.insetGray, borderRadius: BorderRadius.circular(Radii.chip)),
                child: Text(
                  summary.value?.source == TeamSummaryOutSource.ai ? 'AI' : 'Rules',
                  style: AppText.readout.copyWith(fontSize: 10),
                ),
              ),
              Expanded(
                child: Text(summary.value?.text ?? '…', key: const Key('summary'), style: AppText.bodySmall),
              ),
              IconButton(
                key: const Key('regenerate'),
                tooltip: 'Regenerate',
                visualDensity: VisualDensity.compact,
                icon: _regenerating ? const Spinner(radius: 8) : const Icon(Icons.refresh, size: 20),
                onPressed: _regenerating
                    ? null
                    : () async {
                        setState(() => _regenerating = true);
                        try {
                          await ref.read(teamsRepositoryProvider).refreshSummary(widget.team.id);
                        } catch (_) {}
                        ref.invalidate(teamSummaryProvider(widget.team.id));
                        if (mounted) setState(() => _regenerating = false);
                      },
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------- grades

class _GradesCard extends StatelessWidget {
  const _GradesCard({required this.rating});

  final TeamRating rating;

  @override
  Widget build(BuildContext context) => Section(
    title: 'Grades',
    trailing: Text('worst first', style: AppText.label.copyWith(color: Palette.mutedSlate)),
    child: Column(
      children: [
        for (final a in [...rating.areas]..sort((x, y) => x.score.compareTo(y.score)))
          Padding(
            key: Key('area-${a.key.json}'),
            padding: const EdgeInsets.symmetric(vertical: 6),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                GradeBadge(a.grade.json ?? '?', size: 28),
                const SizedBox(width: Space.sm),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(child: Text(a.label, style: AppText.title)),
                          Text('${a.score}', style: AppText.readout),
                        ],
                      ),
                      Text(a.headline, style: AppText.bodySmall.copyWith(color: Palette.inkDim)),
                      if (a.fix != null)
                        Padding(
                          padding: const EdgeInsets.only(top: 2),
                          child: Text(
                            'Fix: ${a.fix}',
                            style: AppText.bodySmall.copyWith(color: gradeTextColor(a.grade.json ?? '')),
                          ),
                        ),
                    ],
                  ),
                ),
              ],
            ),
          ),
      ],
    ),
  );
}

// ---------------------------------------------------------------- how it plays

class _HowItPlays extends ConsumerWidget {
  const _HowItPlays({required this.teamId});

  final int teamId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(teamStrategyProvider(teamId));
    return Section(
      title: 'How it plays',
      child: switch (s) {
        AsyncData(:final value) => Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Reads as ${value.style.toLowerCase()}: ${value.styleReason}.',
              style: AppText.bodySmall.copyWith(color: Palette.inkDim),
            ),
            const SizedBox(height: Space.sm),
            for (final ax in value.axes)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  children: [
                    SizedBox(width: 64, child: Text(ax.label, style: AppText.bodySmall)),
                    Expanded(
                      child: _AxisBar(now: ax.now, potential: ax.potential),
                    ),
                    SizedBox(
                      width: 64,
                      child: Text(
                        ax.now == ax.potential ? '${ax.now}' : '${ax.now} / ${ax.potential}',
                        textAlign: TextAlign.right,
                        style: AppText.readout.copyWith(fontSize: 12),
                      ),
                    ),
                  ],
                ),
              ),
            Text(
              'Solid = now; light = with learnable moves.',
              style: AppText.bodySmall.copyWith(color: Palette.mutedSlate, fontSize: 11),
            ),
          ],
        ),
        AsyncError(:final error) => SectionError(
          error: error,
          onRetry: () => ref.invalidate(teamStrategyProvider(teamId)),
        ),
        _ => const LinearProgressIndicator(minHeight: 2),
      },
    );
  }
}

class _AxisBar extends StatelessWidget {
  const _AxisBar({required this.now, required this.potential});

  final int now;
  final int potential;

  @override
  Widget build(BuildContext context) => ClipRRect(
    borderRadius: BorderRadius.circular(Radii.pill),
    child: SizedBox(
      height: 8,
      child: Stack(
        children: [
          Container(color: Palette.insetGray),
          FractionallySizedBox(
            widthFactor: (potential / 100).clamp(0, 1),
            child: Container(color: Palette.youBlue.withValues(alpha: 0.25)),
          ),
          FractionallySizedBox(
            widthFactor: (now / 100).clamp(0, 1),
            child: Container(color: Palette.youBlue),
          ),
        ],
      ),
    ),
  );
}

// ---------------------------------------------------------------- type profile

const _allTypes = [
  'normal',
  'fire',
  'water',
  'electric',
  'grass',
  'ice',
  'fighting',
  'poison',
  'ground',
  'flying',
  'psychic',
  'bug',
  'rock',
  'ghost',
  'dragon',
  'dark',
  'steel',
  'fairy',
];

/// A report group: a small label line, then its content (the matchup layout).
Widget _group(String label, Widget child, {bool first = false}) => Container(
  margin: EdgeInsets.only(top: first ? 0 : 10),
  padding: EdgeInsets.only(top: first ? 0 : 10),
  decoration: BoxDecoration(
    border: first ? null : const Border(top: BorderSide(color: Palette.hairlineSoft)),
  ),
  child: Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        label,
        style: AppText.label.copyWith(fontSize: 11.5, fontWeight: FontWeight.w500, color: Palette.mutedSlate),
      ),
      const SizedBox(height: 6),
      child,
    ],
  ),
);

class _TypeProfile extends StatelessWidget {
  const _TypeProfile({required this.p});

  final TeamProfile p;

  @override
  Widget build(BuildContext context) {
    Widget chips(List<Widget> c, String empty) => c.isEmpty
        ? Text(empty, style: AppText.bodySmall.copyWith(color: Palette.inkDim))
        : Wrap(spacing: 6, runSpacing: 6, children: c);
    // Hitting nearly everything is the point; name only what it misses.
    final misses = [
      for (final t in _allTypes)
        if (!p.strongVs.contains(t)) t,
    ];
    return Section(
      title: 'Type profile',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _group(
            'Weak to',
            chips([for (final w in p.weakTo) TypeChip(w.type, count: w.net)], 'No shared weaknesses'),
            first: true,
          ),
          _group(
            'Resists',
            chips([for (final r in p.resists) TypeChip(r.type, count: r.net)], 'Nothing in particular'),
          ),
          _group(
            'Hits hard',
            misses.isEmpty
                ? Text('Every type', style: AppText.body)
                : misses.length <= 6
                ? Wrap(
                    spacing: 6,
                    runSpacing: 6,
                    crossAxisAlignment: WrapCrossAlignment.center,
                    children: [
                      Text(
                        '${p.strongVs.length} of 18 types · misses',
                        style: AppText.body.copyWith(color: Palette.inkDim),
                      ),
                      for (final t in misses) TypeChip(t),
                    ],
                  )
                : chips([for (final t in p.strongVs) TypeChip(t)], 'Nothing super effective'),
          ),
          if (p.coreTypes.isNotEmpty) _group('Core', chips([for (final t in p.coreTypes.take(3)) TypeChip(t)], '')),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------- sets

class _SetsCard extends ConsumerStatefulWidget {
  const _SetsCard({required this.team, required this.a});

  final TeamOut team;
  final TeamAnalysis a;

  @override
  ConsumerState<_SetsCard> createState() => _SetsCardState();
}

class _SetsCardState extends ConsumerState<_SetsCard> {
  int? _busy;

  /// Fills only what the member is missing with the engine's suggestion (as the website).
  Future<void> _use(TeamMemberOut m, SlotSuggestion s) async {
    setState(() => _busy = m.slot);
    try {
      await ref
          .read(teamsRepositoryProvider)
          .applyBuild(
            widget.team.id,
            m.slot,
            SlotBuild(
              moves: m.moves.isNotEmpty ? null : s.recommendedMoves.map((x) => x.name).toList(),
              ability: m.ability != null ? null : s.recommendedAbility,
              nature: m.nature != null ? null : s.recommendedNature,
              item: m.item != null ? null : s.recommendedItem,
              evs: m.evSpread.isNotEmpty ? null : s.recommendedEvs,
            ),
          );
      invalidateTeamW(ref, widget.team.id);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Couldn't apply the suggestion: $e")));
      }
    } finally {
      if (mounted) setState(() => _busy = null);
    }
  }

  @override
  Widget build(BuildContext context) {
    final members = [...widget.team.members]..sort((x, y) => x.slot.compareTo(y.slot));
    final sug = {for (final s in widget.a.suggestions) s.slot: s};
    final sug_ = AppText.bodySmall.copyWith(color: Palette.mutedSlate, fontStyle: FontStyle.italic);
    return Section(
      title: 'Sets',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          for (final m in members)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 6),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(m.name, style: AppText.bodySmall.copyWith(fontWeight: FontWeight.w700)),
                        Text.rich(
                          TextSpan(
                            style: AppText.bodySmall,
                            children: [
                              m.item != null
                                  ? TextSpan(text: m.item!.name)
                                  : TextSpan(text: sug[m.slot]?.recommendedItem ?? '—', style: sug_),
                              const TextSpan(text: ' · '),
                              m.ability != null
                                  ? TextSpan(text: m.ability!.name)
                                  : TextSpan(text: sug[m.slot]?.recommendedAbility ?? '—', style: sug_),
                              const TextSpan(text: ' · '),
                              m.moves.isNotEmpty
                                  ? TextSpan(text: '${m.moves.length}/4 moves')
                                  : TextSpan(
                                      text: sug[m.slot]?.recommendedMoves.map((x) => x.name).join(', ') ?? 'no moves',
                                      style: sug_,
                                    ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  if ((m.item == null || m.ability == null || m.moves.isEmpty) && sug[m.slot] != null)
                    TextButton(
                      key: Key('use-suggested-${m.slot}'),
                      onPressed: _busy == m.slot ? null : () => _use(m, sug[m.slot]!),
                      child: Text(_busy == m.slot ? 'Saving…' : 'Use suggested'),
                    ),
                ],
              ),
            ),
          Text(
            'Grey italics = suggested, not set yet. "Use suggested" fills only the empty parts.',
            style: AppText.bodySmall.copyWith(color: Palette.mutedSlate, fontSize: 11),
          ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------- defence

class _DefenceCard extends StatefulWidget {
  const _DefenceCard({required this.rating, required this.a});

  final TeamRating rating;
  final TeamAnalysis a;

  @override
  State<_DefenceCard> createState() => _DefenceCardState();
}

class _DefenceCardState extends State<_DefenceCard> {
  bool all = false;

  @override
  Widget build(BuildContext context) {
    final rows = [...widget.rating.threats.where((t) => t.weak > 0)]
      ..sort((x, y) => (y.weak - y.resist).compareTo(x.weak - x.resist));
    // The problems first; the evened-out rest one tap away.
    final problems = rows.where((t) => t.weak > t.resist).toList();
    final shown = all || problems.isEmpty ? rows : problems;
    String who(String type, bool weak) => widget.a.defensive.matrix
        .where((m) => weak ? (m.multipliers[type] ?? 1) >= 2 : (m.multipliers[type] ?? 1) < 1)
        .map((m) => m.name)
        .join(', ');
    return Section(
      title: 'Defence',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (problems.isEmpty)
            Text(
              'No type hits more of the team than it resists.',
              style: AppText.bodySmall.copyWith(color: Palette.inkDim),
            ),
          for (final (i, t) in shown.indexed)
            Container(
              padding: const EdgeInsets.symmetric(vertical: 9),
              decoration: BoxDecoration(
                border: i == 0 ? null : const Border(top: BorderSide(color: Palette.hairlineSoft)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      TypeChip(t.type),
                      const Spacer(),
                      Text(
                        t.weak > t.resist
                            ? '${t.weak - t.resist} more weak'
                            : (t.weak == t.resist ? 'Even' : 'Covered'),
                        style: AppText.label.copyWith(color: t.problem ? Palette.pokeballRedText : Palette.mutedSlate),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text('Weak: ${who(t.type, true)}', style: AppText.bodySmall.copyWith(color: Palette.instrumentInk)),
                  if (t.resist > 0)
                    Text(
                      'Resists: ${who(t.type, false)}',
                      style: AppText.bodySmall.copyWith(color: Palette.mutedSlate),
                    ),
                ],
              ),
            ),
          if (!all && rows.length > shown.length)
            Align(
              alignment: Alignment.centerLeft,
              child: TextButton(
                key: const Key('defence-all'),
                onPressed: () => setState(() => all = true),
                child: Text('Show the other ${rows.length - shown.length}'),
              ),
            ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------- matchup

/// With an opponent: the server's verdict, scorecard, their threats, our pressure and advice.
class MatchupCard extends ConsumerWidget {
  const MatchupCard({super.key, required this.teamId, required this.opponentId});

  final int teamId;
  final int opponentId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final a = ref.watch(teamAnalysisProvider((teamId, opponentId)));
    return switch (a) {
      AsyncData(:final value) when value.vsOpponent != null => _matchup(value.vsOpponent!),
      AsyncData() => const SizedBox.shrink(),
      AsyncError(:final error) => SectionError(
        error: error,
        onRetry: () => ref.invalidate(teamAnalysisProvider((teamId, opponentId))),
      ),
      _ => const LinearProgressIndicator(minHeight: 2),
    };
  }

  Widget _matchup(VsOpponent vs) {
    final v = vs.verdict;
    return Section(
      title: 'vs ${vs.opponentName}',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (v != null) ...[
            Text(v.label, key: const Key('verdict'), style: AppText.headline),
            Text(v.reason, style: AppText.bodySmall.copyWith(color: Palette.inkDim)),
            const SizedBox(height: Space.sm),
          ],
          for (final r in vs.scorecard)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Row(
                children: [
                  Expanded(child: Text(r.label, style: AppText.bodySmall)),
                  Text(r.oursLabel, style: AppText.readout.copyWith(fontSize: 12, color: Palette.youBlueText)),
                  Text('  /  ', style: AppText.readout.copyWith(fontSize: 12, color: Palette.faintSlate)),
                  Text(r.theirsLabel, style: AppText.readout.copyWith(fontSize: 12, color: Palette.pokeballRedText)),
                ],
              ),
            ),
          if (vs.threats.isNotEmpty) ...[
            const SizedBox(height: Space.sm),
            Text('Their threats', style: AppText.label.copyWith(color: Palette.mutedSlate)),
            for (final t in vs.threats)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 3),
                child: Text(
                  '${t.opponentName} threatens ${t.threatens.join(', ')} (${t.via.join(', ')})',
                  style: AppText.bodySmall,
                ),
              ),
          ],
          if (vs.ourPressure.isNotEmpty) ...[
            const SizedBox(height: Space.sm),
            Text('Our pressure', style: AppText.label.copyWith(color: Palette.mutedSlate)),
            for (final p in vs.ourPressure)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 3),
                child: Text(
                  '${p.attacker} hits ${p.targets.join(', ')} (${p.via.join(', ')})',
                  style: AppText.bodySmall,
                ),
              ),
          ],
          if (vs.advice.isNotEmpty) ...[
            const SizedBox(height: Space.sm),
            Text('Advice', style: AppText.label.copyWith(color: Palette.mutedSlate)),
            for (final x in vs.advice)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 3),
                child: Text('• $x', style: AppText.bodySmall),
              ),
          ],
        ],
      ),
    );
  }
}
