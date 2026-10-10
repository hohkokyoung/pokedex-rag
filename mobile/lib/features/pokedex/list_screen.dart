import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../api/export.dart';
import '../../data/errors.dart';
import '../../data/pokedex_repository.dart';
import '../../data/server.dart';
import '../../data/sprites.dart';
import '../../theme/theme.dart';
import '../../theme/tokens.g.dart';
import '../../widgets/artwork.dart';
import '../../widgets/cant_reach.dart';
import '../../widgets/type_chip.dart';
import '../../widgets/ui.dart';
import 'filters_sheet.dart';
import 'list_state.dart';

class ListScreen extends ConsumerStatefulWidget {
  const ListScreen({super.key});

  @override
  ConsumerState<ListScreen> createState() => _ListScreenState();
}

class _ListScreenState extends ConsumerState<ListScreen> {
  final _search = TextEditingController();
  Timer? _debounce;

  @override
  void initState() {
    super.initState();
    _search.text = ref.read(listQueryProvider).q;
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _search.dispose();
    super.dispose();
  }

  void _onSearch(String text) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 250), () {
      final q = ref.read(listQueryProvider);
      if (q.q != text.trim()) ref.read(listQueryProvider.notifier).set(q.copyWith(q: text.trim()));
    });
  }

  @override
  Widget build(BuildContext context) {
    final query = ref.watch(listQueryProvider);
    final list = ref.watch(pokedexListProvider);
    final filters = query.types.length + query.generations.length;
    final sorted = query.sort != 'dex' || query.descending;
    return Scaffold(
      body: SafeArea(
        bottom: false,
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(Space.gutter, Space.xs, Space.gutter, 0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(
                    children: [
                      const BrandMark(),
                      const Spacer(),
                      SquareButton(
                        key: const Key('open-favourites'),
                        tooltip: 'Favourites',
                        icon: Icons.favorite_border,
                        onPressed: () => context.push('/favourites'),
                      ),
                      const SizedBox(width: 8),
                      SquareButton(tooltip: 'Server', icon: Icons.dns_outlined, onPressed: () => context.push('/settings')),
                    ],
                  ),
                  const SizedBox(height: Space.sm),
                  const PageTitle('Pokédex'),
                  const SizedBox(height: Space.md),
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          key: const Key('search'),
                          controller: _search,
                          onChanged: _onSearch,
                          textInputAction: TextInputAction.search,
                          autocorrect: false,
                          decoration: const InputDecoration(
                            prefixIcon: Icon(Icons.search, color: Palette.mutedSlate),
                            hintText: 'Search by name or dex number',
                            isDense: true,
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Badge(
                        isLabelVisible: filters > 0 || sorted,
                        label: filters > 0 ? Text('$filters') : null,
                        backgroundColor: Palette.pokeballRed,
                        child: SquareButton(
                          key: const Key('filters'),
                          tooltip: 'Filter and sort',
                          icon: Icons.tune,
                          size: 48,
                          onPressed: () => showFiltersSheet(context),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  const _TypeStrip(),
                ],
              ),
            ),
            Expanded(
              child: switch (list) {
                AsyncData(:final value) => _Results(state: value, query: query),
                AsyncError(:final error) => _ErrorState(error: error),
                _ => const Center(child: CircularProgressIndicator()),
              },
            ),
          ],
        ),
      ),
    );
  }
}

/// One tap filters by a type (up to two, as the filter sheet allows); the website's type toggles.
class _TypeStrip extends ConsumerWidget {
  const _TypeStrip();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final types = ref.watch(typeOptionsProvider).value ?? const <String>[];
    final q = ref.watch(listQueryProvider);
    if (types.isEmpty) return const SizedBox(height: 32);
    return SizedBox(
      height: 32,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: types.length,
        separatorBuilder: (_, _) => const SizedBox(width: 6),
        itemBuilder: (_, i) {
          final t = types[i];
          final on = q.types.contains(t);
          return TypeToggle(
            key: Key('strip-$t'),
            type: t,
            selected: on,
            onChanged: (_) {
              final next = on ? q.types.where((x) => x != t).toList() : [...q.types, t];
              ref.read(listQueryProvider.notifier).set(q.copyWith(types: next.length > 2 ? next.sublist(next.length - 2) : next));
            },
          );
        },
      ),
    );
  }
}

class _ErrorState extends ConsumerWidget {
  const _ErrorState({required this.error});

  final Object error;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    void retry() => ref.invalidate(pokedexListProvider);
    if (error is Unreachable) return CantReach(address: (error as Unreachable).address, onRetry: retry);
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text('The server had a problem loading the Pokédex.', style: AppText.body),
          const SizedBox(height: Space.sm),
          FilledButton(onPressed: retry, child: const Text('Retry')),
        ],
      ),
    );
  }
}

class _Results extends ConsumerWidget {
  const _Results({required this.state, required this.query});

  final ListState state;
  final ListQuery query;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (state.items.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('No Pokémon match.', style: AppText.title),
            if (query.isFiltered) ...[
              const SizedBox(height: Space.sm),
              TextButton(
                key: const Key('clear-filters'),
                onPressed: () => ref.read(listQueryProvider.notifier).clearFilters(),
                child: const Text('Clear search and filters'),
              ),
            ],
          ],
        ),
      );
    }
    final base = ref.watch(serverAddressProvider);
    final footer = !state.done || state.moreFailed != null;
    return NotificationListener<ScrollNotification>(
      onNotification: (n) {
        if (n.metrics.extentAfter < 600) ref.read(pokedexListProvider.notifier).loadMore();
        return false;
      },
      // Keyed by the query: new results start at the top, not at the old scroll position.
      child: CustomScrollView(
        key: ValueKey(('pokedex-list', query)),
        slivers: [
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(Space.gutter + 2, Space.md, Space.gutter + 2, 8),
            sliver: SliverToBoxAdapter(
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      '${_count(state.total)} Pokémon',
                      key: const Key('result-count'),
                      style: AppText.bodySmall.copyWith(color: Palette.mutedSlate),
                    ),
                  ),
                  Text(_sortLabel(query), style: AppText.readout.copyWith(fontSize: 12, color: Palette.mutedSlate)),
                ],
              ),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(Space.gutter, 0, Space.gutter, Space.gutter),
            sliver: SliverGrid(
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                mainAxisSpacing: 10,
                crossAxisSpacing: 10,
                mainAxisExtent: 226,
              ),
              delegate: SliverChildBuilderDelegate(
                (context, i) {
                  // Nearing the end of what's loaded (also covers a first page shorter than the screen).
                  if (i >= state.items.length - 6 && !state.done && state.moreFailed == null) {
                    WidgetsBinding.instance.addPostFrameCallback((_) => ref.read(pokedexListProvider.notifier).loadMore());
                  }
                  return DexCard(p: state.items[i], base: base, sort: query.sort);
                },
                childCount: state.items.length,
              ),
            ),
          ),
          if (footer) SliverToBoxAdapter(child: _footer(ref)),
        ],
      ),
    );
  }

  /// The end of the grid: progress while the next page loads (the grid asks for it as its
  /// last cards build), or a retry after a failed page.
  Widget _footer(WidgetRef ref) => state.moreFailed == null
      ? (state.loadingMore
          ? const Padding(padding: EdgeInsets.all(Space.lg), child: Center(child: CircularProgressIndicator()))
          : const SizedBox(height: Space.lg))
      : Center(
          child: TextButton(
            onPressed: () => ref.read(pokedexListProvider.notifier).loadMore(),
            child: const Text("Couldn't load more. Tap to retry."),
          ),
        );

  static String _count(int n) => n.toString().replaceAllMapped(RegExp(r'(\d)(?=(\d{3})+$)'), (m) => '${m[1]},');

  static String _sortLabel(ListQuery q) {
    final name = switch (q.sort) {
      'name' => 'by name',
      'total' => 'by total',
      'hp' => 'by HP',
      'attack' => 'by Attack',
      'defense' => 'by Defense',
      'sp_attack' => 'by Sp. Atk',
      'sp_defense' => 'by Sp. Def',
      'speed' => 'by Speed',
      _ => 'by dex',
    };
    return '$name ${q.descending ? '↓' : '↑'}';
  }
}

/// The website's catalog card: dex number, the sorted number (labelled), artwork on a
/// soft glow of its first type, name, genus and type chips.
class DexCard extends StatelessWidget {
  const DexCard({super.key, required this.p, required this.base, this.sort = 'dex'});

  final PokemonSummary p;
  final String base;
  final String sort;

  /// The number the card leads with: the sorted-by stat, else the base stat total.
  (String, int) get _metric {
    final s = p.stats;
    return switch (sort) {
      'hp' => ('HP', s?.hp ?? 0),
      'attack' => ('Attack', s?.attack ?? 0),
      'defense' => ('Defense', s?.defense ?? 0),
      'sp_attack' => ('Sp. Atk', s?.spAttack ?? 0),
      'sp_defense' => ('Sp. Def', s?.spDefense ?? 0),
      'speed' => ('Speed', s?.speed ?? 0),
      _ => ('Total', p.baseStatTotal),
    };
  }

  @override
  Widget build(BuildContext context) {
    final target = p.formId != null ? '/pokemon/${p.dexNumber}?form=${p.formId}' : '/pokemon/${p.dexNumber}';
    final tint = TypeColors.fill[p.types.firstOrNull] ?? Palette.mutedSlate;
    final (label, value) = _metric;
    return Card(
      key: Key('dex-card-${p.id}'),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: () => context.push(target),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(12, 10, 12, 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Text('#${p.dexNumber.toString().padLeft(4, '0')}', style: AppText.readout.copyWith(color: Palette.faintSlate)),
                  ),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text('$value', style: AppText.readout.copyWith(fontSize: 15, height: 1, color: Palette.instrumentInk)),
                      Text(label, style: AppText.label.copyWith(fontSize: 10.5, color: Palette.faintSlate)),
                    ],
                  ),
                ],
              ),
              Expanded(
                child: Center(
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      gradient: RadialGradient(colors: [tint.withValues(alpha: .28), tint.withValues(alpha: 0)], stops: const [0, .7]),
                    ),
                    child: Hero(tag: 'art-${p.formId ?? p.dexNumber}', child: Artwork(thumbUrl(base, p.spriteUrl), size: 96)),
                  ),
                ),
              ),
              Text(p.name, maxLines: 1, overflow: TextOverflow.ellipsis, style: AppText.title),
              if (p.genus != null)
                Text(
                  p.genus!,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: AppText.bodySmall.copyWith(color: Palette.mutedSlate),
                ),
              const SizedBox(height: 6),
              Wrap(spacing: 4, runSpacing: 4, children: [for (final t in p.types) TypeChip(t, dense: true)]),
            ],
          ),
        ),
      ),
    );
  }
}
