import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../theme/theme.dart';
import '../../theme/tokens.g.dart';
import '../../widgets/ui.dart';
import 'list_state.dart';

/// The backend's sorts, in the website's order.
const sorts = {
  'dex': 'Dex number',
  'name': 'Name',
  'total': 'Total',
  'hp': 'HP',
  'attack': 'Attack',
  'defense': 'Defense',
  'sp_attack': 'Sp. Atk',
  'sp_defense': 'Sp. Def',
  'speed': 'Speed',
};

String _cap(String t) => t.isEmpty ? t : t[0].toUpperCase() + t.substring(1);

/// The Pokédex's filters as one row of pills: Type, Generation and Sort. Each opens its
/// own sheet, and every change applies at once and reloads the list from the top.
class ListFilterBar extends ConsumerWidget {
  const ListFilterBar({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final q = ref.watch(listQueryProvider);
    final gens = ref.watch(generationOptionsProvider).value ?? const [];
    final genName = {for (final g in gens) g.id: g.name.replaceFirst('Generation ', 'Gen ')};
    final sorted = q.sort != 'dex' || q.descending;
    return Wrap(
      spacing: 6,
      runSpacing: 6,
      children: [
        FilterPill(
          key: const Key('filter-type'),
          label: q.types.isEmpty ? 'Type' : q.types.map(_cap).join(' + '),
          on: q.types.isNotEmpty,
          onTap: () => _types(context),
        ),
        FilterPill(
          key: const Key('filter-gen'),
          label: switch (q.generations.length) {
            0 => 'Generation',
            1 => genName[q.generations.single] ?? 'Generation',
            final n => '$n generations',
          },
          on: q.generations.isNotEmpty,
          onTap: () => _gens(context, ref),
        ),
        FilterPill(
          key: const Key('filter-sort'),
          label: sorts[q.sort] ?? q.sort,
          on: sorted,
          icon: q.descending ? Icons.arrow_downward : Icons.arrow_upward,
          onTap: () => _sort(context),
        ),
      ],
    );
  }

  void _types(BuildContext context) => showPanelSheet(
    context,
    title: 'Type',
    builder: (_) => Consumer(
      builder: (context, ref, _) {
        final q = ref.watch(listQueryProvider);
        final types = ref.watch(typeOptionsProvider).value ?? const <String>[];
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('Up to two; a Pokémon must have both.', style: AppText.bodySmall.copyWith(color: Palette.mutedSlate)),
            const SizedBox(height: Space.sm),
            TypeGrid(
              types: types,
              selected: q.types,
              max: 2,
              onChanged: (next) => ref.read(listQueryProvider.notifier).set(q.copyWith(types: next)),
            ),
          ],
        );
      },
    ),
  );

  void _gens(BuildContext context, WidgetRef ref) {
    final q = ref.read(listQueryProvider);
    final gens = ref.read(generationOptionsProvider).value ?? const [];
    final byLabel = {for (final g in gens) g.name: g.id};
    showChoices<int>(
      context,
      title: 'Generation',
      many: true,
      options: [for (final g in gens) (g.id, g.name, null)],
      selected: {...q.generations},
      keyOf: (label) => 'gen-${byLabel[label]}',
      onChanged: (s) {
        final now = ref.read(listQueryProvider);
        ref.read(listQueryProvider.notifier).set(now.copyWith(generations: s.toList()..sort()));
      },
    );
  }

  void _sort(BuildContext context) => showPanelSheet(
    context,
    title: 'Sort',
    builder: (_) => Consumer(
      builder: (context, ref, _) {
        final q = ref.watch(listQueryProvider);
        final set = ref.read(listQueryProvider.notifier).set;
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Segmented<bool>(
              key: const Key('order'),
              value: q.descending,
              onChanged: (d) => set(q.copyWith(descending: d)),
              options: const [
                (false, 'Lowest first', Key('order-asc')),
                (true, 'Highest first', Key('order-desc')),
              ],
            ),
            const SizedBox(height: Space.xs),
            for (final e in sorts.entries)
              ChoiceRow(
                key: Key('sort-${e.key}'),
                label: e.value,
                selected: q.sort == e.key,
                onTap: () {
                  set(q.copyWith(sort: e.key));
                  Navigator.of(context).pop();
                },
              ),
          ],
        );
      },
    ),
  );
}

/// A type filter drawn as the type's own chip (solid colour, name written out), so
/// filters and results read the same. Picked ones carry a check; while any type is
/// picked, the others fade.
class TypeToggle extends StatelessWidget {
  const TypeToggle({super.key, required this.type, required this.selected, required this.onChanged, this.dimmed = false, this.expand = false});

  final String type;
  final bool selected;
  final ValueChanged<bool> onChanged;

  /// Another type is picked and this one isn't.
  final bool dimmed;

  /// Fill the width it's given (a grid cell).
  final bool expand;

  @override
  Widget build(BuildContext context) {
    final fill = TypeColors.fill[type] ?? Palette.mutedSlate;
    final on = TypeColors.on[type] ?? Palette.panelWhite;
    final still = MediaQuery.of(context).disableAnimations;
    return Semantics(
      button: true,
      selected: selected,
      label: type,
      excludeSemantics: true,
      child: Pressable(
        onTap: () {
          HapticFeedback.selectionClick();
          onChanged(!selected);
        },
        child: AnimatedOpacity(
          duration: still ? Duration.zero : const Duration(milliseconds: 160),
          opacity: dimmed ? .45 : 1,
          child: Container(
            height: 34,
            padding: const EdgeInsets.symmetric(horizontal: 10),
            decoration: BoxDecoration(color: fill, borderRadius: BorderRadius.circular(Radii.chip)),
            child: Row(
              mainAxisSize: expand ? MainAxisSize.max : MainAxisSize.min,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                if (selected) ...[Icon(Icons.check, size: 14, color: on), const SizedBox(width: 4)],
                Flexible(
                  child: Text(
                    type[0].toUpperCase() + type.substring(1),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: AppText.label.copyWith(color: on),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// Every type as a three-column grid of type chips: the phone's way to pick types
/// (no strip running off the edge). [max] keeps the newest picks.
class TypeGrid extends StatelessWidget {
  const TypeGrid({super.key, required this.types, required this.selected, required this.onChanged, this.max, this.keyPrefix = 'type'});

  final List<String> types;
  final List<String> selected;
  final ValueChanged<List<String>> onChanged;
  final int? max;
  final String keyPrefix;

  @override
  Widget build(BuildContext context) => LayoutBuilder(
    builder: (context, c) {
      const gap = 6.0;
      final w = (c.maxWidth - gap * 2) / 3;
      return Wrap(
        spacing: gap,
        runSpacing: gap,
        children: [
          for (final t in types)
            SizedBox(
              width: w,
              child: TypeToggle(
                key: Key('$keyPrefix-$t'),
                type: t,
                expand: true,
                selected: selected.contains(t),
                dimmed: selected.isNotEmpty && !selected.contains(t),
                onChanged: (on) {
                  final next = [...selected]..remove(t);
                  if (on) next.add(t);
                  onChanged(max != null && next.length > max! ? next.sublist(next.length - max!) : next);
                },
              ),
            ),
        ],
      );
    },
  );
}
