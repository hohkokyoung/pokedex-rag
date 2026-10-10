// The details a lookup row opens: a move, an ability with who has it, an item.
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../api/export.dart';
import '../../data/pokedex_repository.dart' show failureOf;
import '../../data/server.dart';
import '../../data/sprites.dart';
import '../../theme/theme.dart';
import '../../theme/tokens.g.dart';
import '../../widgets/artwork.dart';
import '../../widgets/type_chip.dart';
import '../pokedex/detail_more.dart' show showMoveSheet;

final abilityHoldersProvider = FutureProvider.autoDispose.family<List<AbilityHolderOut>, int>((ref, id) async {
  final dio = ref.watch(dioProvider);
  try {
    return await PokeragClient(dio).abilityHoldersApiAbilitiesAbilityIdPokemonGet(abilityId: id);
  } on DioException catch (e) {
    throw failureOf(e, dio.options.baseUrl);
  }
});

/// A move's details and who learns it, in any game (from the lookup or the finder).
void openMove(BuildContext context, MoveOut m) => showMoveSheet(
      context,
      GameMoveOut(
        identifier: m.identifier, moveId: m.id, name: m.name, priority: m.priority, accuracy: m.accuracy,
        damageClass: m.damageClass, power: m.power, pp: m.pp, shortEffect: m.shortEffect, type: m.type,
      ),
      null,
    );

/// An ability's or item's details in a draggable sheet over the tab bar.
void showLookupSheet(BuildContext context, Widget Function(ScrollController) build) => showModalBottomSheet<void>(
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
