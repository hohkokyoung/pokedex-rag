import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../api/export.dart';
import '../../data/errors.dart';
import '../../data/pokedex_repository.dart' show failureOf;
import '../../data/server.dart';
import '../../data/sprites.dart';
import '../../theme/theme.dart';
import '../../theme/tokens.g.dart';
import '../../widgets/ui.dart';
import '../../widgets/artwork.dart';
import '../../widgets/cant_reach.dart';
import '../../widgets/type_chip.dart';
import '../pokedex/detail_more.dart' show showMoveSheet;

typedef LookupResults = ({List<MoveOut> moves, List<AbilityOut> abilities, List<ItemOut> items});

/// Moves, abilities and items whose name matches [q] (empty: the first of each).
final lookupProvider = FutureProvider.autoDispose.family<LookupResults, String>((ref, q) async {
  final dio = ref.watch(dioProvider);
  final api = PokeragClient(dio);
  final query = q.isEmpty ? null : q;
  try {
    final (moves, abilities, items) = await (
      api.searchMovesApiMovesGet(q: query, limit: 20),
      api.searchAbilitiesApiAbilitiesGet(q: query, limit: 10),
      api.searchItemsApiItemsGet(q: query, limit: 10),
    ).wait;
    return (moves: moves, abilities: abilities, items: items);
  } on ParallelWaitError catch (e) {
    final err = (e.errors as (AsyncError?, AsyncError?, AsyncError?)).$1 ?? e.errors.$2 ?? e.errors.$3;
    final cause = err?.error;
    throw cause is DioException ? failureOf(cause, dio.options.baseUrl) : cause ?? e;
  }
});

final abilityHoldersProvider = FutureProvider.autoDispose.family<List<AbilityHolderOut>, int>((ref, id) async {
  final dio = ref.watch(dioProvider);
  try {
    return await PokeragClient(dio).abilityHoldersApiAbilitiesAbilityIdPokemonGet(abilityId: id);
  } on DioException catch (e) {
    throw failureOf(e, dio.options.baseUrl);
  }
});

class LookupScreen extends ConsumerStatefulWidget {
  const LookupScreen({super.key});

  @override
  ConsumerState<LookupScreen> createState() => _LookupScreenState();
}

class _LookupScreenState extends ConsumerState<LookupScreen> {
  Timer? _debounce;
  String q = '';

  @override
  void dispose() {
    _debounce?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final results = ref.watch(lookupProvider(q));
    return Scaffold(
      appBar: pageBar('Lookup'),
      body: Column(children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(Space.gutter, 0, Space.gutter, Space.sm),
          child: TextField(
            key: const Key('lookup-field'),
            autocorrect: false,
            onChanged: (v) {
              _debounce?.cancel();
              _debounce = Timer(const Duration(milliseconds: 200), () => setState(() => q = v.trim()));
            },
            decoration: const InputDecoration(
              prefixIcon: Icon(Icons.search),
              hintText: 'Earthquake, Intimidate, Leftovers…',
              isDense: true,
            ),
          ),
        ),
        Expanded(
          child: switch (results) {
            AsyncData(:final value) => _list(value),
            AsyncError(:final error) when error is Unreachable =>
              CantReach(address: error.address, onRetry: () => ref.invalidate(lookupProvider(q))),
            AsyncError() => Center(child: Text('The server had a problem searching.', style: AppText.body)),
            _ => const Center(child: CircularProgressIndicator()),
          },
        ),
      ]),
    );
  }

  Widget _list(LookupResults r) {
    if (r.moves.isEmpty && r.abilities.isEmpty && r.items.isEmpty) {
      return Center(child: Text('Nothing matches “$q”.', style: AppText.body));
    }
    Widget head(String t) => Padding(
          padding: const EdgeInsets.only(top: Space.md, bottom: 2),
          child: Text(t, style: AppText.label.copyWith(color: Palette.mutedSlate)),
        );
    return ListView(
      padding: const EdgeInsets.fromLTRB(Space.gutter, 0, Space.gutter, Space.gutter * 2),
      children: [
        if (r.moves.isNotEmpty) head('Moves'),
        for (final m in r.moves)
          ListTile(
            key: Key('look-move-${m.id}'),
            contentPadding: EdgeInsets.zero,
            dense: true,
            title: Text(m.name, style: AppText.bodySmall.copyWith(fontWeight: FontWeight.w700)),
            subtitle: m.shortEffect == null ? null : Text(m.shortEffect!, maxLines: 2, overflow: TextOverflow.ellipsis, style: AppText.bodySmall),
            trailing: m.type == null ? null : TypeChip(m.type!, dense: true),
            onTap: () => showMoveSheet(
              context,
              GameMoveOut(
                identifier: m.identifier, moveId: m.id, name: m.name, priority: m.priority, accuracy: m.accuracy,
                damageClass: m.damageClass, power: m.power, pp: m.pp, shortEffect: m.shortEffect, type: m.type,
              ),
              null,
            ),
          ),
        if (r.abilities.isNotEmpty) head('Abilities'),
        for (final a in r.abilities)
          ListTile(
            key: Key('look-ability-${a.id}'),
            contentPadding: EdgeInsets.zero,
            dense: true,
            title: Text(a.name, style: AppText.bodySmall.copyWith(fontWeight: FontWeight.w700)),
            subtitle: Text(a.shortEffect ?? a.effect ?? '', maxLines: 2, overflow: TextOverflow.ellipsis, style: AppText.bodySmall),
            onTap: () => _sheet((scroll) => AbilitySheet(ability: a, scroll: scroll)),
          ),
        if (r.items.isNotEmpty) head('Items'),
        for (final i in r.items)
          ListTile(
            key: Key('look-item-${i.id}'),
            contentPadding: EdgeInsets.zero,
            dense: true,
            title: Text(i.name, style: AppText.bodySmall.copyWith(fontWeight: FontWeight.w700)),
            subtitle: Text(i.shortEffect ?? '', maxLines: 2, overflow: TextOverflow.ellipsis, style: AppText.bodySmall),
            onTap: () => _sheet((scroll) => ItemSheet(item: i, scroll: scroll)),
          ),
      ],
    );
  }

  void _sheet(Widget Function(ScrollController) build) => showModalBottomSheet<void>(
        context: context,
        useRootNavigator: true,
        isScrollControlled: true,
        showDragHandle: true,
        backgroundColor: Palette.panelWhite,
        builder: (_) => DraggableScrollableSheet(
          expand: false,
          initialChildSize: 0.7,
          maxChildSize: 0.95,
          builder: (_, scroll) => build(scroll),
        ),
      );
}

/// An ability's effect and the Pokémon that have it (filterable), each opening its page.
class AbilitySheet extends ConsumerStatefulWidget {
  const AbilitySheet({super.key, required this.ability, required this.scroll});

  final AbilityOut ability;
  final ScrollController scroll;

  @override
  ConsumerState<AbilitySheet> createState() => _AbilitySheetState();
}

class _AbilitySheetState extends ConsumerState<AbilitySheet> {
  String filter = '';

  @override
  Widget build(BuildContext context) {
    final a = widget.ability;
    final holders = ref.watch(abilityHoldersProvider(a.id));
    final base = ref.watch(serverAddressProvider);
    return ListView(
      controller: widget.scroll,
      padding: const EdgeInsets.fromLTRB(Space.gutter, 0, Space.gutter, Space.gutter * 2),
      children: [
        Text(a.name, style: AppText.headline),
        const SizedBox(height: Space.xs),
        Text(a.shortEffect ?? a.effect ?? '', key: const Key('ability-effect'), style: AppText.body),
        if (a.shortEffect != null && a.effect != null && a.effect != a.shortEffect) ...[
          const SizedBox(height: Space.xs),
          Text(a.effect!, style: AppText.bodySmall.copyWith(color: Palette.inkDim)),
        ],
        const SizedBox(height: Space.md),
        TextField(
          key: const Key('holders-filter'),
          autocorrect: false,
          onChanged: (v) => setState(() => filter = v.trim().toLowerCase()),
          decoration: const InputDecoration(prefixIcon: Icon(Icons.filter_list), hintText: 'Filter Pokémon', isDense: true),
        ),
        const SizedBox(height: Space.xs),
        switch (holders) {
          AsyncData(:final value) => Column(children: [
              Align(
                alignment: Alignment.centerLeft,
                child: Text('${value.length} Pokémon have it', style: AppText.label.copyWith(color: Palette.mutedSlate)),
              ),
              for (final h in value.where((h) => filter.isEmpty || h.name.toLowerCase().contains(filter)))
                ListTile(
                  key: Key('holder-${h.id}'),
                  contentPadding: EdgeInsets.zero,
                  dense: true,
                  leading: Artwork(thumbUrl(base, h.spriteUrl), size: 36),
                  title: Text('${h.name}${h.isHidden ? ' (hidden)' : ''}', style: AppText.bodySmall.copyWith(fontWeight: FontWeight.w600)),
                  trailing: Wrap(spacing: 4, children: [for (final t in h.types) TypeChip(t, dense: true)]),
                  onTap: () {
                    Navigator.of(context).pop();
                    context.push(h.id > 10000 ? '/pokemon/${h.dexNumber}?form=${h.id}' : '/pokemon/${h.dexNumber}');
                  },
                ),
            ]),
          AsyncError() => Text("Couldn't load who has it.", style: AppText.bodySmall.copyWith(color: Palette.pokeballRedText)),
          _ => const LinearProgressIndicator(minHeight: 2),
        },
      ],
    );
  }
}

/// An item's effect, category, cost and Fling power.
class ItemSheet extends StatelessWidget {
  const ItemSheet({super.key, required this.item, required this.scroll});

  final ItemOut item;
  final ScrollController scroll;

  @override
  Widget build(BuildContext context) {
    final i = item;
    String cap(String s) => s.replaceAll('-', ' ').replaceFirstMapped(RegExp('^.'), (m) => m[0]!.toUpperCase());
    return ListView(
      controller: scroll,
      padding: const EdgeInsets.fromLTRB(Space.gutter, 0, Space.gutter, Space.gutter * 2),
      children: [
        Text(i.name, style: AppText.headline),
        const SizedBox(height: Space.xs),
        Text(
          [
            if (i.category != null) cap(i.category!),
            if (i.cost != null && i.cost! > 0) '₽${i.cost}',
            if (i.flingPower != null) 'Fling power ${i.flingPower}',
          ].join(' · '),
          key: const Key('item-facts'),
          style: AppText.readout.copyWith(color: Palette.inkDim),
        ),
        const SizedBox(height: Space.sm),
        if (i.shortEffect != null) Text(i.shortEffect!, key: const Key('item-effect'), style: AppText.body),
        if (i.flavorText != null) ...[
          const SizedBox(height: Space.sm),
          Text(i.flavorText!, style: AppText.bodySmall.copyWith(color: Palette.inkDim)),
        ],
      ],
    );
  }
}
