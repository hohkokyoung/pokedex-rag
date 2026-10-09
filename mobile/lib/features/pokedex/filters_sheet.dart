import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/pokedex_repository.dart';
import '../../theme/theme.dart';
import '../../theme/tokens.g.dart';
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

Future<void> showFiltersSheet(BuildContext context) => showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      backgroundColor: Palette.panelWhite,
      builder: (_) => const FiltersSheet(),
    );

/// Types (up to two, all must match), generations (any may match) and sort. Every
/// change applies at once and reloads the list from the top.
class FiltersSheet extends ConsumerWidget {
  const FiltersSheet({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final q = ref.watch(listQueryProvider);
    final set = ref.read(listQueryProvider.notifier).set;
    final types = ref.watch(typeOptionsProvider).value ?? const [];
    final gens = ref.watch(generationOptionsProvider).value ?? const [];

    Widget section(String title, Widget child) => Padding(
          padding: const EdgeInsets.only(bottom: Space.lg),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(title, style: AppText.label.copyWith(color: Palette.mutedSlate)),
            const SizedBox(height: Space.xs),
            child,
          ]),
        );

    return SafeArea(
      child: ConstrainedBox(
        constraints: BoxConstraints(maxHeight: MediaQuery.sizeOf(context).height * 0.8),
        child: ListView(
          shrinkWrap: true,
          padding: const EdgeInsets.fromLTRB(Space.gutter, 0, Space.gutter, Space.gutter),
          children: [
            section(
              'Sort',
              Wrap(spacing: 6, runSpacing: 6, children: [
                for (final e in sorts.entries)
                  ChoiceChip(
                    key: Key('sort-${e.key}'),
                    label: Text(e.value),
                    selected: q.sort == e.key,
                    onSelected: (_) => set(q.copyWith(sort: e.key)),
                  ),
                ChoiceChip(
                  key: const Key('order'),
                  avatar: Icon(q.descending ? Icons.arrow_downward : Icons.arrow_upward, size: 16),
                  label: Text(q.descending ? 'Highest first' : 'Lowest first'),
                  selected: q.descending,
                  onSelected: (v) => set(q.copyWith(descending: v)),
                ),
              ]),
            ),
            section(
              'Type · up to two',
              Wrap(spacing: 6, runSpacing: 6, children: [
                for (final t in types)
                  TypeToggle(
                    key: Key('type-$t'),
                    type: t,
                    selected: q.types.contains(t),
                    onChanged: (on) {
                      final next = [...q.types]..remove(t);
                      if (on) next.add(t);
                      set(q.copyWith(types: next.length > 2 ? next.sublist(next.length - 2) : next));
                    },
                  ),
              ]),
            ),
            section(
              'Generation',
              Wrap(spacing: 6, runSpacing: 6, children: [
                for (final g in gens)
                  FilterChip(
                    key: Key('gen-${g.id}'),
                    label: Text(g.name.replaceFirst('Generation ', 'Gen ')),
                    selected: q.generations.contains(g.id),
                    onSelected: (on) {
                      final next = [...q.generations]..remove(g.id);
                      if (on) next.add(g.id);
                      set(q.copyWith(generations: next..sort()));
                    },
                  ),
              ]),
            ),
            if (q.isFiltered || q.sort != 'dex' || q.descending)
              Align(
                alignment: Alignment.centerLeft,
                child: TextButton(onPressed: () => set(const ListQuery()), child: const Text('Reset all')),
              ),
          ],
        ),
      ),
    );
  }
}

/// A type filter: the type's own colour when on (like its chip), its text colour on white
/// when off. The name is always written out.
class TypeToggle extends StatelessWidget {
  const TypeToggle({super.key, required this.type, required this.selected, required this.onChanged});

  final String type;
  final bool selected;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) {
    final fill = TypeColors.fill[type] ?? Palette.mutedSlate;
    return Semantics(
      button: true,
      selected: selected,
      child: Material(
        color: selected ? fill : Palette.panelWhite,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(Radii.control),
          side: BorderSide(color: selected ? fill : Palette.hairline),
        ),
        child: InkWell(
          borderRadius: BorderRadius.circular(Radii.control),
          onTap: () => onChanged(!selected),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: Text(
              type[0].toUpperCase() + type.substring(1),
              style: AppText.label.copyWith(
                fontSize: 14,
                color: selected ? (TypeColors.on[type] ?? Palette.panelWhite) : (TypeColors.text[type] ?? Palette.inkDim),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
