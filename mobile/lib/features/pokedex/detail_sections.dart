import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../api/export.dart';
import '../../data/sprites.dart';
import '../../theme/theme.dart';
import '../../theme/tokens.g.dart';
import '../../widgets/artwork.dart';
import '../../widgets/type_chip.dart';
import 'detail_screen.dart';
import 'detail_state.dart';

/// A titled panel, like the website's detail cards.
class Section extends StatelessWidget {
  const Section({super.key, required this.title, required this.child, this.trailing});

  final String title;
  final Widget child;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) => Card(
        child: Padding(
          padding: const EdgeInsets.all(Space.md),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Expanded(child: Text(title, style: AppText.headline)),
              ?trailing,
            ]),
            const SizedBox(height: Space.sm),
            child,
          ]),
        ),
      );
}

// ---------------------------------------------------------------- stats

class StatsCard extends StatelessWidget {
  const StatsCard({super.key, required this.stats, required this.still, this.tint});

  final StatsOut stats;
  final bool still;

  /// The Pokémon's first type colour (the website's stat bars); without one, bars show the value's tone.
  final Color? tint;

  static const max = 255;

  @override
  Widget build(BuildContext context) {
    final rows = [
      ('HP', stats.hp),
      ('Attack', stats.attack),
      ('Defense', stats.defense),
      ('Sp. Atk', stats.spAttack),
      ('Sp. Def', stats.spDefense),
      ('Speed', stats.speed),
    ];
    return Section(
      title: 'Base stats',
      trailing: Text('Total ${stats.total}', key: const Key('stat-total'), style: AppText.readout.copyWith(fontSize: 13)),
      child: Column(children: [
        for (final (label, value) in rows)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Row(children: [
              SizedBox(width: 64, child: Text(label, style: AppText.bodySmall.copyWith(color: Palette.inkDim))),
              SizedBox(width: 36, child: Text('$value', textAlign: TextAlign.right, style: AppText.readout.copyWith(fontSize: 13))),
              const SizedBox(width: Space.sm),
              Expanded(child: _StatBar(value: value, still: still, tint: tint)),
            ]),
          ),
      ]),
    );
  }
}

/// Draws in from zero once; with reduced motion it starts at its value.
class _StatBar extends StatelessWidget {
  const _StatBar({required this.value, required this.still, this.tint});

  final int value;
  final bool still;
  final Color? tint;

  Color get _tone => tint ?? (value >= 120
      ? Palette.verdictGreen
      : value >= 80
          ? Palette.youBlue
          : value >= 50
              ? Palette.cautionAmber
              : Palette.pokeballRed);

  @override
  Widget build(BuildContext context) => ClipRRect(
        borderRadius: BorderRadius.circular(Radii.pill),
        child: Container(
          height: 8,
          color: Palette.insetGray,
          alignment: Alignment.centerLeft,
          child: TweenAnimationBuilder<double>(
            tween: Tween(begin: still ? value / StatsCard.max : 0, end: value / StatsCard.max),
            duration: still ? Duration.zero : const Duration(milliseconds: 900),
            curve: Curves.easeOutExpo,
            builder: (_, f, _) => FractionallySizedBox(
              key: const Key('stat-fill'),
              widthFactor: f.clamp(0, 1),
              child: Container(color: _tone),
            ),
          ),
        ),
      );
}

// ---------------------------------------------------------------- abilities

class AbilitiesCard extends StatelessWidget {
  const AbilitiesCard({super.key, required this.abilities});

  final List<AbilityView> abilities;

  @override
  Widget build(BuildContext context) => Section(
        title: 'Abilities',
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          for (final a in abilities)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 6),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(children: [
                  Text(a.name, style: AppText.title),
                  if (a.hidden) ...[
                    const SizedBox(width: Space.xs),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                      decoration: BoxDecoration(color: Palette.insetGray, borderRadius: BorderRadius.circular(Radii.chip)),
                      child: Text('Hidden', style: AppText.readout.copyWith(fontSize: 10, color: Palette.mutedSlate)),
                    ),
                  ],
                ]),
                if (a.effect != null && a.effect!.isNotEmpty)
                  Text(a.effect!, style: AppText.bodySmall.copyWith(color: Palette.inkDim)),
              ]),
            ),
        ]),
      );
}

// ---------------------------------------------------------------- matchups

/// How a matchup group reads: its multiplier colour (the website's `.mu` tones).
enum MatchTone { bad, good, immune, hit }

const _toneColor = {
  MatchTone.bad: Palette.pokeballRedText,
  MatchTone.good: Palette.verdictGreenText,
  MatchTone.immune: Color(0xFF4A505C),
  MatchTone.hit: Palette.youBlueText,
};

/// One group: its label, then rows of (multiplier, types, row key).
typedef MatchGroup = (MatchTone, String, List<(String, List<String>, Key?)>);

/// Type matchups as the website shows them on a phone: each group's label on its own
/// line, then its rows (a coloured multiplier and the type chips); groups split by a
/// hairline, and only rows with types appear.
class MatchupGroups extends StatelessWidget {
  const MatchupGroups({super.key, required this.groups});

  final List<MatchGroup> groups;

  @override
  Widget build(BuildContext context) {
    final shown = [
      for (final (tone, label, rows) in groups)
        if (rows.any((r) => r.$2.isNotEmpty)) (tone, label, rows.where((r) => r.$2.isNotEmpty).toList()),
    ];
    if (shown.isEmpty) {
      return Text('Perfectly neutral: no notable weaknesses or resistances.', style: AppText.bodySmall.copyWith(color: Palette.mutedSlate));
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final (i, (tone, label, rows)) in shown.indexed)
          Container(
            margin: EdgeInsets.only(top: i == 0 ? 0 : 10),
            padding: EdgeInsets.only(top: i == 0 ? 0 : 10),
            decoration: BoxDecoration(border: i == 0 ? null : const Border(top: BorderSide(color: Palette.hairlineSoft))),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: AppText.label.copyWith(fontSize: 11.5, fontWeight: FontWeight.w500, color: Palette.mutedSlate)),
                for (final (mult, types, key) in rows)
                  Padding(
                    key: key,
                    padding: const EdgeInsets.only(top: 6),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        SizedBox(
                          width: 30,
                          child: Padding(
                            padding: const EdgeInsets.only(top: 2),
                            child: Text(mult, style: AppText.readout.copyWith(fontSize: 13, color: _toneColor[tone])),
                          ),
                        ),
                        Expanded(child: Wrap(spacing: 6, runSpacing: 6, children: [for (final t in types) TypeChip(t)])),
                      ],
                    ),
                  ),
              ],
            ),
          ),
      ],
    );
  }
}

/// The defensive groups for a matchup result, plus "Hits ×2" when [hits] is given.
List<MatchGroup> matchGroups({
  required List<String> x4,
  required List<String> x2,
  required List<String> half,
  required List<String> quarter,
  required List<String> immune,
  List<String>? hits,
  String keyPrefix = 'mu',
  Key? hitsKey,
}) => [
  (MatchTone.bad, 'Takes more from', [('×4', x4, Key('$keyPrefix-x4')), ('×2', x2, Key('$keyPrefix-x2'))]),
  (MatchTone.good, 'Resists', [('×½', half, Key('$keyPrefix-half')), ('×¼', quarter, Key('$keyPrefix-quarter'))]),
  (MatchTone.immune, 'Immune to', [('×0', immune, Key('$keyPrefix-immune'))]),
  if (hits != null) (MatchTone.hit, 'Hits', [('×2', hits, hitsKey ?? Key('$keyPrefix-hits'))]),
];

class MatchupsCard extends ConsumerWidget {
  const MatchupsCard({super.key, required this.matchups, required this.types});

  final MatchupsOut matchups;
  final List<String> types;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final chart = ref.watch(typeChartProvider);
    return Section(
      title: 'Type matchups',
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        // "Hits ×2": what the Pokémon's own types hit super-effectively, from the served chart.
        MatchupGroups(
          groups: matchGroups(
            x4: matchups.weak4x,
            x2: matchups.weak2x,
            half: matchups.resistHalf,
            quarter: matchups.resistQuarter,
            immune: matchups.immune,
            hits: chart.value == null ? null : _hits(chart.value!),
            hitsKey: const Key('hits-row'),
          ),
        ),
        if (chart.isLoading)
          const Padding(
            key: Key('hits-loading'),
            padding: EdgeInsets.only(top: 6),
            child: LinearProgressIndicator(minHeight: 2),
          ),
      ]),
    );
  }

  List<String> _hits(TypeChartOut c) =>
      [for (final d in c.order) if (types.any((t) => (c.chart[t]?[d] ?? 1) >= 2)) d];
}

// ---------------------------------------------------------------- evolution

class EvolutionCard extends StatelessWidget {
  const EvolutionCard({super.key, required this.members, required this.stages, required this.currentId, required this.base});

  final List<EvolutionMember> members;
  final List<EvolutionStage> stages;
  final int currentId;
  final String base;

  @override
  Widget build(BuildContext context) {
    final byId = {for (final m in members) m.id: m};
    final steps = [
      for (final s in stages)
        if (s.fromId != null && byId.containsKey(s.fromId) && byId.containsKey(s.toId)) s,
    ];
    return Section(
      title: 'Evolution',
      child: Column(children: [
        for (final s in steps)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 6),
            child: Row(children: [
              _Member(m: byId[s.fromId]!, current: s.fromId == currentId, base: base),
              Expanded(child: Center(child: _Requirement(display: s.display))),
              _Member(m: byId[s.toId]!, current: s.toId == currentId, base: base),
            ]),
          ),
      ]),
    );
  }
}

class _Member extends StatelessWidget {
  const _Member({required this.m, required this.current, required this.base});

  final EvolutionMember m;
  final bool current;
  final String base;

  @override
  Widget build(BuildContext context) {
    final target = m.formId != null ? '/pokemon/${m.dexNumber}?form=${m.formId}' : '/pokemon/${m.dexNumber}';
    return InkWell(
      borderRadius: BorderRadius.circular(Radii.inset),
      onTap: current ? null : () => context.push(target),
      child: Container(
        width: 84,
        padding: const EdgeInsets.all(4),
        decoration: current
            ? BoxDecoration(color: Palette.insetGray, borderRadius: BorderRadius.circular(Radii.inset))
            : null,
        child: Column(children: [
          Artwork(thumbUrl(base, m.spriteUrl), size: 48),
          Text(m.name, textAlign: TextAlign.center, maxLines: 2, overflow: TextOverflow.ellipsis,
              style: AppText.bodySmall.copyWith(fontWeight: current ? FontWeight.w700 : null)),
        ]),
      ),
    );
  }
}

/// The step's chips exactly as the server labels them; the description is a tap away.
class _Requirement extends StatelessWidget {
  const _Requirement({required this.display});

  final EvolutionDisplay? display;

  @override
  Widget build(BuildContext context) {
    final d = display;
    if (d == null || d.chips.isEmpty) return const Icon(Icons.arrow_forward, size: 18, color: Palette.faintSlate);
    final chips = Wrap(
      alignment: WrapAlignment.center,
      crossAxisAlignment: WrapCrossAlignment.center,
      spacing: 4,
      runSpacing: 4,
      children: [
        for (final (i, c) in d.chips.indexed) ...[
          if (i > 0) Text('+', style: AppText.readout.copyWith(color: Palette.mutedSlate)),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
            decoration: BoxDecoration(
              color: c.tone == EvolutionChipTone.solid ? Palette.instrumentInk : Palette.insetGray,
              borderRadius: BorderRadius.circular(Radii.chip),
            ),
            child: Text(c.label, style: AppText.label.copyWith(
              fontSize: 11.5,
              color: c.tone == EvolutionChipTone.solid ? Palette.panelWhite : Palette.instrumentInk,
            )),
          ),
        ],
        if (d.description != null)
          Semantics(
            button: true,
            label: 'Explain this requirement',
            child: InkResponse(
              key: const Key('evo-explain'),
              radius: 18,
              onTap: () => showModalBottomSheet<void>(
                context: context,
                showDragHandle: true,
                backgroundColor: Palette.panelWhite,
                builder: (_) => SafeArea(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(Space.gutter, 0, Space.gutter, Space.gutter * 2),
                    child: Text(d.description!, style: AppText.body),
                  ),
                ),
              ),
              child: const Icon(Icons.help_outline, size: 18, color: Palette.mutedSlate),
            ),
          ),
      ],
    );
    return Column(mainAxisSize: MainAxisSize.min, children: [
      chips,
      const Icon(Icons.arrow_forward, size: 16, color: Palette.faintSlate),
    ]);
  }
}

// ---------------------------------------------------------------- spin guide

class SpinGuideCard extends StatelessWidget {
  const SpinGuideCard({super.key, required this.guide});

  final SpinGuide guide;

  @override
  Widget build(BuildContext context) {
    final label = AppText.label.copyWith(color: Palette.mutedSlate);
    return Section(
      title: 'How Alcremie gets its look',
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        for (final (i, step) in guide.steps.indexed)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 3),
            child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              SizedBox(width: 22, child: Text('${i + 1}', style: AppText.readout.copyWith(color: Palette.mutedSlate))),
              Expanded(child: Text(step, style: AppText.bodySmall)),
            ]),
          ),
        const SizedBox(height: Space.md),
        Text('Sweet · the topping (${guide.toppings.length})', style: label),
        const SizedBox(height: Space.xs),
        for (final t in guide.toppings)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 2),
            child: Row(children: [
              Expanded(child: Text(t.sweet, style: AppText.bodySmall)),
              Text('${t.topping} topping', style: AppText.bodySmall.copyWith(color: Palette.inkDim)),
            ]),
          ),
        const SizedBox(height: Space.md),
        Text('Cream · how to spin (${guide.creams.length})', style: label),
        const SizedBox(height: Space.xs),
        // Two lines per cream: a four-column table is too tight at phone width.
        for (final c in guide.creams)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(c.cream, style: AppText.bodySmall.copyWith(fontWeight: FontWeight.w700)),
              Text(
                '${c.direction == CreamRuleDirection.clockwise ? '↻' : '↺'} ${c.direction.json ?? ''}'
                ' · ${c.duration} · ${c.time}',
                style: AppText.bodySmall.copyWith(color: Palette.inkDim),
              ),
            ]),
          ),
        const SizedBox(height: Space.xs),
        Text('Rules from Pokémon Sword & Shield. Day and night follow the in-game clock.',
            style: AppText.bodySmall.copyWith(color: Palette.mutedSlate)),
      ]),
    );
  }
}
