import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../api/export.dart';
import '../../data/errors.dart';
import '../../data/server.dart';
import '../../data/sprites.dart';
import '../../theme/theme.dart';
import '../../theme/tokens.g.dart';
import '../../widgets/artwork.dart';
import '../../widgets/cant_reach.dart';
import '../../widgets/type_chip.dart';
import '../../widgets/ui.dart';
import 'detail_more.dart';
import 'detail_sections.dart';
import 'favourites.dart';
import 'detail_state.dart';

class DetailScreen extends ConsumerWidget {
  const DetailScreen({super.key, required this.id, this.formId});

  final String id;
  final int? formId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final detail = ref.watch(detailProvider(id));
    final d = detail.value;
    final total = ref.watch(dexTotalProvider).value;
    return Scaffold(
      appBar: AppBar(
        toolbarHeight: 52,
        actions: [
          if (d != null && d.dexNumber > 1)
            _StepButton(
              key: const Key('prev'),
              label: '‹ ${(d.dexNumber - 1).toString().padLeft(4, '0')}',
              tooltip: 'Previous',
              onPressed: () => context.replace('/pokemon/${d.dexNumber - 1}'),
            ),
          const SizedBox(width: 6),
          if (d != null && total != null && d.dexNumber < total)
            _StepButton(
              key: const Key('next'),
              label: '${(d.dexNumber + 1).toString().padLeft(4, '0')} ›',
              tooltip: 'Next',
              onPressed: () => context.replace('/pokemon/${d.dexNumber + 1}'),
            ),
          const SizedBox(width: Space.gutter),
        ],
      ),
      body: switch (detail) {
        AsyncData(:final value) => DetailBody(detail: value, formId: formId),
        AsyncError(:final error) => switch (error) {
            Unreachable(:final address) => CantReach(address: address, onRetry: () => ref.invalidate(detailProvider(id))),
            NotFound() => Center(child: Text('No Pokémon “$id”.', style: AppText.body)),
            _ => Center(child: Text('The server had a problem loading this Pokémon.', style: AppText.body)),
          },
        _ => const Center(child: CircularProgressIndicator()),
      },
    );
  }
}

/// What the page shows: the species, or one of its forms when `?form=` picks it.
class DetailView {
  DetailView(this.detail, this.form);

  final PokemonDetail detail;
  final FormOut? form;

  String get name => form?.name ?? detail.name;
  List<String> get types => form?.types ?? detail.types;
  StatsOut get stats => form?.stats ?? detail.stats;
  MatchupsOut get matchups => form?.matchups ?? detail.matchups;
  String get spriteUrl => form?.spriteUrl ?? detail.spriteUrl;
  List<AbilityView> get abilities => form != null
      ? [for (final a in form!.abilities) AbilityView(a.name, a.isHidden, a.effect)]
      : [for (final a in detail.abilities) AbilityView(a.name, a.isHidden, a.shortEffect ?? a.effect)];

  /// A form with its own evolution line shows that line; otherwise the species'.
  bool get _formChain => form != null && form!.evolutionMembers.length > 1;
  List<EvolutionMember> get evoMembers => _formChain ? form!.evolutionMembers : detail.evolutionMembers;
  List<EvolutionStage> get evoStages => _formChain ? form!.evolutionStages : detail.evolutionStages;
  SpinGuide? get spinGuide => _formChain ? form!.spinGuide : detail.spinGuide;
  int get currentId => form?.id ?? detail.id;
}

class AbilityView {
  const AbilityView(this.name, this.hidden, this.effect);
  final String name;
  final bool hidden;
  final String? effect;
}

enum DetailPart { overview, moves, evolution, where }

/// The website's hero, then the page in segments (Overview / Moves / Evolution / Where).
class DetailBody extends ConsumerStatefulWidget {
  const DetailBody({super.key, required this.detail, this.formId});

  final PokemonDetail detail;
  final int? formId;

  @override
  ConsumerState<DetailBody> createState() => _DetailBodyState();
}

class _DetailBodyState extends ConsumerState<DetailBody> {
  DetailPart part = DetailPart.overview;

  @override
  Widget build(BuildContext context) {
    final detail = widget.detail;
    final form = widget.formId == null ? null : detail.forms.where((f) => f.id == widget.formId).firstOrNull;
    final view = DetailView(detail, form);
    final base = ref.watch(serverAddressProvider);
    final still = MediaQuery.disableAnimationsOf(context);
    final entries = form?.flavorEntries.isNotEmpty == true ? form!.flavorEntries : detail.flavorEntries;
    const gap = SizedBox(height: Space.sm);
    final cards = switch (part) {
      DetailPart.overview => [
          StatsCard(key: ValueKey(('stats', view.currentId)), stats: view.stats, still: still, tint: TypeColors.fill[view.types.firstOrNull]),
          gap,
          AbilitiesCard(abilities: view.abilities),
          gap,
          MatchupsCard(matchups: view.matchups, types: view.types),
          gap,
          FactsCard(d: detail, form: form),
        ],
      DetailPart.moves => [MovesetCard(key: ValueKey(('moves', view.currentId)), pokemonId: view.currentId)],
      DetailPart.evolution => [
          if (view.evoMembers.length > 1)
            EvolutionCard(members: view.evoMembers, stages: view.evoStages, currentId: view.currentId, base: base)
          else
            Section(title: 'Evolution', child: Text('${view.name} doesn’t evolve.', style: AppText.body.copyWith(color: Palette.inkDim))),
          if (view.spinGuide != null) ...[gap, SpinGuideCard(guide: view.spinGuide!)],
        ],
      DetailPart.where => [
          if (entries.isNotEmpty) ...[DexEntriesCard(entries: entries), gap],
          EncountersCard(key: ValueKey(('enc', view.currentId)), pokemonId: view.currentId),
        ],
    };
    return CustomScrollView(slivers: [
      SliverPadding(
        padding: const EdgeInsets.symmetric(horizontal: Space.gutter),
        sliver: SliverToBoxAdapter(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            if (detail.forms.isNotEmpty) _FormSwitcher(detail: detail, selected: form?.id),
            _Hero(view: view, base: base, still: still),
            _Identity(view: view),
          ]),
        ),
      ),
      SliverPersistentHeader(
        pinned: true,
        delegate: _PinnedSegments(
          Segmented<DetailPart>(
            key: const Key('detail-parts'),
            value: part,
            onChanged: (p) => setState(() => part = p),
            options: const [
              (DetailPart.overview, 'Overview', Key('part-overview')),
              (DetailPart.moves, 'Moves', Key('part-moves')),
              (DetailPart.evolution, 'Evolution', Key('part-evolution')),
              (DetailPart.where, 'Where', Key('part-where')),
            ],
          ),
        ),
      ),
      SliverPadding(
        padding: const EdgeInsets.fromLTRB(Space.gutter, Space.xs, Space.gutter, Space.gutter * 3),
        sliver: SliverList(delegate: SliverChildListDelegate(cards)),
      ),
    ]);
  }
}

/// Keeps the segments under the top bar while the page scrolls, on the ground's colour.
class _PinnedSegments extends SliverPersistentHeaderDelegate {
  _PinnedSegments(this.child);

  final Widget child;
  static const _h = 44.0 + Space.sm * 2;

  @override
  double get minExtent => _h;
  @override
  double get maxExtent => _h;

  @override
  Widget build(BuildContext context, double shrinkOffset, bool overlapsContent) => Container(
        color: overlapsContent || shrinkOffset > 0 ? const Color(0xF2EBE9F0) : Colors.transparent,
        padding: const EdgeInsets.symmetric(horizontal: Space.gutter, vertical: Space.sm),
        child: child,
      );

  @override
  bool shouldRebuild(covariant _PinnedSegments oldDelegate) => oldDelegate.child != child;
}

/// The website's detail hero: the artwork on a glow of its first type, over its ghosted
/// dex number. The artwork arrives from the list card (Hero) and settles once.
class _Hero extends StatelessWidget {
  const _Hero({required this.view, required this.base, required this.still});

  final DetailView view;
  final String base;
  final bool still;

  @override
  Widget build(BuildContext context) {
    final tint = TypeColors.fill[view.types.firstOrNull] ?? Palette.mutedSlate;
    final no = '#${view.detail.dexNumber.toString().padLeft(4, '0')}';
    return SizedBox(
      height: 280,
      child: Stack(alignment: Alignment.center, children: [
        Container(
          width: 300,
          height: 300,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: RadialGradient(colors: [tint.withValues(alpha: .42), tint.withValues(alpha: 0)], stops: const [0, .68]),
          ),
        ),
        ExcludeSemantics(
          child: Text(no,
              maxLines: 1,
              softWrap: false,
              overflow: TextOverflow.clip,
              style: AppText.display.copyWith(fontSize: 104, fontWeight: FontWeight.w700, color: tint.withValues(alpha: .16), height: 1)),
        ),
        Hero(
          tag: 'art-${view.form?.id ?? view.detail.dexNumber}',
          child: TweenAnimationBuilder<double>(
            key: ValueKey(view.spriteUrl),
            tween: Tween(begin: still ? 1 : 0.94, end: 1),
            duration: still ? Duration.zero : const Duration(milliseconds: 500),
            curve: const Cubic(0.16, 1, 0.3, 1),
            builder: (_, t, child) => Transform.scale(scale: t, child: child),
            child: Artwork(spriteUrl(base, view.spriteUrl), size: 240),
          ),
        ),
      ]),
    );
  }
}

/// Dex number and generation, name with the favourite beside it, genus, types.
class _Identity extends StatelessWidget {
  const _Identity({required this.view});

  final DetailView view;

  @override
  Widget build(BuildContext context) {
    final d = view.detail;
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(
        ['#${d.dexNumber.toString().padLeft(4, '0')}', ?d.generation?.name].join(' · '),
        style: AppText.readout.copyWith(fontSize: 12, color: Palette.mutedSlate),
      ),
      const SizedBox(height: 2),
      Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
        Expanded(child: Text(view.name, style: AppText.display.copyWith(fontSize: 36, fontWeight: FontWeight.w700, height: 1.05))),
        FavouriteButton(pokemon: d),
      ]),
      if (d.genus != null) Text(d.genus!, style: AppText.body.copyWith(color: Palette.mutedSlate, fontStyle: FontStyle.italic)),
      const SizedBox(height: Space.sm),
      Wrap(spacing: 6, runSpacing: 6, children: [for (final t in view.types) TypeChip(t)]),
      const SizedBox(height: Space.xs),
    ]);
  }
}

/// Previous / next by dex number: the website's mono step buttons.
class _StepButton extends StatelessWidget {
  const _StepButton({super.key, required this.label, required this.tooltip, required this.onPressed});

  final String label;
  final String tooltip;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) => Tooltip(
        message: tooltip,
        child: Material(
          color: Palette.panelWhite,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(Radii.control), side: const BorderSide(color: Palette.hairline)),
          child: InkWell(
            borderRadius: BorderRadius.circular(Radii.control),
            onTap: onPressed,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 9),
              child: Text(label, style: AppText.readout.copyWith(fontSize: 12, color: Palette.inkDim)),
            ),
          ),
        ),
      );
}

class _FormSwitcher extends StatelessWidget {
  const _FormSwitcher({required this.detail, required this.selected});

  final PokemonDetail detail;
  final int? selected;

  @override
  Widget build(BuildContext context) {
    void go(int? form) => context.replace(form == null ? '/pokemon/${detail.dexNumber}' : '/pokemon/${detail.dexNumber}?form=$form');
    return Wrap(spacing: 6, runSpacing: 6, children: [
      ChoiceChip(key: const Key('form-base'), label: Text(detail.name), selected: selected == null, onSelected: (_) => go(null)),
      for (final f in detail.forms)
        ChoiceChip(key: Key('form-${f.id}'), label: Text(f.name), selected: selected == f.id, onSelected: (_) => go(f.id)),
    ]);
  }
}
