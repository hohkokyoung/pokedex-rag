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
    return Scaffold(
      appBar: AppBar(
        title: Text('pokérag', style: AppText.display.copyWith(fontSize: 26)),
        actions: [
          IconButton(
            key: const Key('open-favourites'),
            tooltip: 'Favourites',
            icon: const Icon(Icons.favorite_border),
            onPressed: () => context.push('/favourites'),
          ),
          IconButton(
            tooltip: 'Server',
            icon: const Icon(Icons.dns_outlined),
            onPressed: () => context.push('/settings'),
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(Space.gutter, 0, Space.gutter, Space.sm),
            child: Row(children: [
              Expanded(
                child: TextField(
                  key: const Key('search'),
                  controller: _search,
                  onChanged: _onSearch,
                  textInputAction: TextInputAction.search,
                  autocorrect: false,
                  decoration: const InputDecoration(
                    prefixIcon: Icon(Icons.search),
                    hintText: 'Name or dex number',
                    isDense: true,
                  ),
                ),
              ),
              const SizedBox(width: Space.sm),
              Badge(
                isLabelVisible: filters > 0 || query.sort != 'dex' || query.descending,
                label: filters > 0 ? Text('$filters') : null,
                backgroundColor: Palette.pokeballRed,
                child: IconButton.outlined(
                  key: const Key('filters'),
                  tooltip: 'Filter and sort',
                  icon: const Icon(Icons.tune),
                  onPressed: () => showFiltersSheet(context),
                ),
              ),
            ]),
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
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        Text('The server had a problem loading the Pokédex.', style: AppText.body),
        const SizedBox(height: Space.sm),
        FilledButton(onPressed: retry, child: const Text('Retry')),
      ]),
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
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Text('No Pokémon match.', style: AppText.title),
          if (query.isFiltered) ...[
            const SizedBox(height: Space.sm),
            TextButton(
              key: const Key('clear-filters'),
              onPressed: () => ref.read(listQueryProvider.notifier).clearFilters(),
              child: const Text('Clear search and filters'),
            ),
          ],
        ]),
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
      child: ListView.separated(
        key: ValueKey(('pokedex-list', query)),
        padding: const EdgeInsets.fromLTRB(Space.gutter, Space.xs, Space.gutter, Space.gutter * 2),
        itemCount: state.items.length + (footer ? 1 : 0),
        separatorBuilder: (_, _) => const SizedBox(height: Space.xs),
        itemBuilder: (context, i) {
          if (i == state.items.length) {
            // Near the end: ask for the next page (also covers a first page shorter than the screen).
            if (state.moreFailed == null) {
              WidgetsBinding.instance.addPostFrameCallback((_) => ref.read(pokedexListProvider.notifier).loadMore());
              return const Padding(padding: EdgeInsets.all(Space.lg), child: Center(child: CircularProgressIndicator()));
            }
            return Center(
              child: TextButton(
                onPressed: () => ref.read(pokedexListProvider.notifier).loadMore(),
                child: const Text("Couldn't load more. Tap to retry."),
              ),
            );
          }
          return PokemonRow(p: state.items[i], base: base, sort: query.sort);
        },
      ),
    );
  }
}

class PokemonRow extends StatelessWidget {
  const PokemonRow({super.key, required this.p, required this.base, this.sort = 'dex'});

  final PokemonSummary p;
  final String base;
  final String sort;

  /// The number the row leads with: the sorted-by stat, else the base stat total.
  (String, int) get _metric {
    final s = p.stats;
    return switch (sort) {
      'hp' => ('HP', s?.hp ?? 0),
      'attack' => ('ATK', s?.attack ?? 0),
      'defense' => ('DEF', s?.defense ?? 0),
      'sp_attack' => ('SPA', s?.spAttack ?? 0),
      'sp_defense' => ('SPD', s?.spDefense ?? 0),
      'speed' => ('SPE', s?.speed ?? 0),
      _ => ('BST', p.baseStatTotal),
    };
  }

  @override
  Widget build(BuildContext context) {
    final target = p.formId != null ? '/pokemon/${p.dexNumber}?form=${p.formId}' : '/pokemon/${p.dexNumber}';
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(Radii.card),
        onTap: () => context.push(target),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: Space.md, vertical: Space.sm),
          child: Row(children: [
            Artwork(thumbUrl(base, p.spriteUrl), size: 48),
            const SizedBox(width: Space.md),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('#${p.dexNumber.toString().padLeft(3, '0')}', style: AppText.readout.copyWith(color: Palette.mutedSlate)),
                Text(p.name, style: AppText.title, overflow: TextOverflow.ellipsis),
                const SizedBox(height: 4),
                Wrap(spacing: 4, runSpacing: 4, children: [for (final t in p.types) TypeChip(t, dense: true)]),
              ]),
            ),
            Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
              Text('${_metric.$2}', style: AppText.readout.copyWith(fontSize: 15, color: Palette.instrumentInk)),
              Text(_metric.$1, style: AppText.readout.copyWith(fontSize: 10, color: Palette.mutedSlate)),
            ]),
          ]),
        ),
      ),
    );
  }
}
