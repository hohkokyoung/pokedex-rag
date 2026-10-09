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
      appBar: AppBar(actions: [
        if (d != null) FavouriteButton(pokemon: d),
        if (d != null && d.dexNumber > 1)
          IconButton(
            key: const Key('prev'),
            tooltip: 'Previous',
            icon: const Icon(Icons.chevron_left),
            onPressed: () => context.replace('/pokemon/${d.dexNumber - 1}'),
          ),
        if (d != null && total != null && d.dexNumber < total)
          IconButton(
            key: const Key('next'),
            tooltip: 'Next',
            icon: const Icon(Icons.chevron_right),
            onPressed: () => context.replace('/pokemon/${d.dexNumber + 1}'),
          ),
      ]),
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

class DetailBody extends ConsumerWidget {
  const DetailBody({super.key, required this.detail, this.formId});

  final PokemonDetail detail;
  final int? formId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final form = formId == null ? null : detail.forms.where((f) => f.id == formId).firstOrNull;
    final view = DetailView(detail, form);
    final base = ref.watch(serverAddressProvider);
    final still = MediaQuery.disableAnimationsOf(context);
    return ListView(
      padding: const EdgeInsets.fromLTRB(Space.gutter, 0, Space.gutter, Space.gutter * 3),
      children: [
        _Header(view: view, base: base, still: still),
        if (detail.forms.isNotEmpty) ...[
          const SizedBox(height: Space.md),
          _FormSwitcher(detail: detail, selected: form?.id),
        ],
        const SizedBox(height: Space.lg),
        StatsCard(key: ValueKey(('stats', view.currentId)), stats: view.stats, still: still),
        const SizedBox(height: Space.md),
        AbilitiesCard(abilities: view.abilities),
        const SizedBox(height: Space.md),
        MatchupsCard(matchups: view.matchups, types: view.types),
        const SizedBox(height: Space.md),
        FactsCard(d: detail, form: form),
        const SizedBox(height: Space.md),
        MovesetCard(key: ValueKey(('moves', view.currentId)), pokemonId: view.currentId),
        if (view.evoMembers.length > 1) ...[
          const SizedBox(height: Space.md),
          EvolutionCard(members: view.evoMembers, stages: view.evoStages, currentId: view.currentId, base: base),
        ],
        if (view.spinGuide != null) ...[
          const SizedBox(height: Space.md),
          SpinGuideCard(guide: view.spinGuide!),
        ],
        if ((form?.flavorEntries ?? detail.flavorEntries).isNotEmpty) ...[
          const SizedBox(height: Space.md),
          DexEntriesCard(entries: form?.flavorEntries.isNotEmpty == true ? form!.flavorEntries : detail.flavorEntries),
        ],
        const SizedBox(height: Space.md),
        EncountersCard(key: ValueKey(('enc', view.currentId)), pokemonId: view.currentId),
      ],
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.view, required this.base, required this.still});

  final DetailView view;
  final String base;
  final bool still;

  @override
  Widget build(BuildContext context) {
    final d = view.detail;
    final art = Artwork(spriteUrl(base, view.spriteUrl), size: 220);
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Center(
        // The artwork settles in once per Pokémon or form; reduced motion shows it at rest.
        child: TweenAnimationBuilder<double>(
          key: ValueKey(view.spriteUrl),
          tween: Tween(begin: still ? 1 : 0.92, end: 1),
          duration: still ? Duration.zero : const Duration(milliseconds: 600),
          curve: Curves.easeOutCubic,
          builder: (_, t, child) => Opacity(opacity: still ? 1 : ((t - 0.92) / 0.08).clamp(0, 1), child: Transform.scale(scale: t, child: child)),
          child: art,
        ),
      ),
      const SizedBox(height: Space.md),
      Text('#${d.dexNumber.toString().padLeft(3, '0')}', style: AppText.readout.copyWith(color: Palette.mutedSlate)),
      Text(view.name, style: AppText.display),
      if (d.genus != null) Text(d.genus!, style: AppText.body.copyWith(color: Palette.inkDim)),
      const SizedBox(height: Space.sm),
      Wrap(spacing: 6, children: [for (final t in view.types) TypeChip(t)]),
    ]);
  }
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
