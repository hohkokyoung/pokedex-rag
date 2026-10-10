import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/export.dart';
import '../../data/errors.dart';
import '../../data/pokedex_repository.dart' show failureOf;
import '../../data/server.dart';
import '../../theme/theme.dart';
import '../../theme/tokens.g.dart';
import '../../widgets/cant_reach.dart';
import '../../widgets/type_chip.dart';
import '../../widgets/ui.dart';
import '../pokedex/filters_sheet.dart' show TypeToggle;
import '../pokedex/list_state.dart' show typeOptionsProvider;
import 'finder_logic.dart';
import 'lookup_screen.dart' show AbilitySheet, ItemSheet, openMove, showLookupSheet;

// Each catalog is fixed at runtime: fetch once per launch (as the website's finder).
Future<T> _load<T>(Ref ref, Future<T> Function(PokeragClient api) call) async {
  final dio = ref.watch(dioProvider);
  try {
    return await call(PokeragClient(dio));
  } on DioException catch (e) {
    throw failureOf(e, dio.options.baseUrl);
  }
}

final allMovesProvider = FutureProvider<List<FinderMove>>(
  (ref) async => foldMoves(await _load(ref, (api) => api.searchMovesApiMovesGet(limit: 2000))),
);
final allAbilitiesProvider = FutureProvider<List<AbilityOut>>(
  (ref) => _load(ref, (api) => api.searchAbilitiesApiAbilitiesGet(limit: 2000)),
);
final allItemsProvider = FutureProvider<List<ItemOut>>(
  (ref) => _load(ref, (api) => api.searchItemsApiItemsGet(limit: 5000)),
);
final moveGamesProvider = FutureProvider<List<MoveGameOut>>(
  (ref) => _load(ref, (api) => api.moveGamesApiMovesGamesGet()),
);

enum FinderKind { moves, abilities, items }

const _roman = ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX'];
const _cats = [('physical', 'Physical'), ('special', 'Special'), ('status', 'Status')];
const _kinds = [(MoveOutKind.regular, 'Regular'), (MoveOutKind.z, 'Z-Move'), (MoveOutKind.max, 'Max Move')];
String _cap(String s) => s.isEmpty ? s : s[0].toUpperCase() + s.substring(1).replaceAll('-', ' ');
String _count(int n) => n.toString().replaceAllMapped(RegExp(r'(\d)(?=(\d{3})+$)'), (m) => '${m[1]},');

/// The website's advanced finder: every move, ability or item with filters and sorting.
/// Picking a row opens the same details as the lookup.
class FinderScreen extends ConsumerStatefulWidget {
  const FinderScreen({super.key});

  @override
  ConsumerState<FinderScreen> createState() => _FinderScreenState();
}

class _FinderScreenState extends ConsumerState<FinderScreen> {
  final _search = TextEditingController();
  FinderKind kind = FinderKind.moves;
  // One search box shared by all three, so switching keeps what you typed.
  String q = '';
  // Moves
  Set<String> types = {};
  Set<String> cats = {};
  Set<MoveOutKind> kinds = {};
  int? game;
  MoveSort moveSort = MoveSort.power;
  bool moveAsc = false;
  // Abilities
  bool abilityAsc = true;
  // Items
  Set<String> itemCats = {};
  ItemSort itemSort = ItemSort.name;
  bool itemAsc = true;

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  bool get _filtered =>
      q.isNotEmpty ||
      switch (kind) {
        FinderKind.moves => types.isNotEmpty || cats.isNotEmpty || kinds.isNotEmpty || game != null,
        FinderKind.items => itemCats.isNotEmpty,
        FinderKind.abilities => false,
      };

  void _clear() => setState(() {
    q = '';
    _search.clear();
    if (kind == FinderKind.moves) {
      types = {};
      cats = {};
      kinds = {};
      game = null;
    }
    if (kind == FinderKind.items) itemCats = {};
  });

  @override
  Widget build(BuildContext context) {
    final moves = ref.watch(allMovesProvider);
    final abilities = ref.watch(allAbilitiesProvider);
    final items = kind == FinderKind.items ? ref.watch(allItemsProvider) : ref.read(allItemsProvider);
    String label(String name, AsyncValue<List<Object?>> v) =>
        v.value == null ? name : '$name ${_count(v.value!.length)}';
    return Scaffold(
      appBar: pageBar('Advanced search'),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(Space.gutter, 0, Space.gutter, 0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Segmented<FinderKind>(
                  key: const Key('finder-kind'),
                  compact: true,
                  value: kind,
                  onChanged: (k) => setState(() => kind = k),
                  options: [
                    (FinderKind.moves, label('Moves', moves), const Key('finder-moves')),
                    (FinderKind.abilities, label('Abilities', abilities), const Key('finder-abilities')),
                    (FinderKind.items, label('Items', items), const Key('finder-items')),
                  ],
                ),
                const SizedBox(height: 8),
                TextField(
                  key: const Key('finder-search'),
                  controller: _search,
                  autocorrect: false,
                  onChanged: (v) => setState(() => q = v),
                  decoration: InputDecoration(
                    isDense: true,
                    prefixIcon: const Icon(Icons.search, color: Palette.mutedSlate),
                    hintText: switch (kind) {
                      FinderKind.moves => 'Search moves',
                      FinderKind.abilities => 'Search abilities or effects',
                      FinderKind.items => 'Search items or effects',
                    },
                  ),
                ),
                const SizedBox(height: 8),
                ...switch (kind) {
                  FinderKind.moves => _moveFilters(),
                  FinderKind.abilities => [
                    Segmented<bool>(
                      key: const Key('ability-order'),
                      compact: true,
                      value: abilityAsc,
                      onChanged: (v) => setState(() => abilityAsc = v),
                      options: const [(true, 'A–Z', null), (false, 'Z–A', null)],
                    ),
                  ],
                  FinderKind.items => _itemFilters(items.value ?? const []),
                },
              ],
            ),
          ),
          Expanded(
            child: switch (kind) {
              FinderKind.moves => _results(moves, (all) => _moveList(all)),
              FinderKind.abilities => _results(abilities, (all) => _abilityList(all)),
              FinderKind.items => _results(items, (all) => _itemList(all)),
            },
          ),
        ],
      ),
    );
  }

  // ------------------------------------------------------------------ filters

  List<Widget> _moveFilters() {
    final typeList = ref.watch(typeOptionsProvider).value ?? const <String>[];
    final games = ref.watch(moveGamesProvider).value ?? const <MoveGameOut>[];
    final gameName = games.where((g) => g.id == game).firstOrNull?.name;
    return [
      SizedBox(
        height: 32,
        child: ListView.separated(
          scrollDirection: Axis.horizontal,
          itemCount: typeList.length,
          separatorBuilder: (_, _) => const SizedBox(width: 6),
          itemBuilder: (_, i) {
            final t = typeList[i];
            return TypeToggle(
              key: Key('finder-type-$t'),
              type: t,
              selected: types.contains(t),
              onChanged: (_) => setState(() => types = types.contains(t) ? ({...types}..remove(t)) : {...types, t}),
            );
          },
        ),
      ),
      const SizedBox(height: 8),
      Wrap(
        spacing: 6,
        runSpacing: 6,
        children: [
          _FilterButton(
            key: const Key('filter-category'),
            label: cats.isEmpty ? 'Category' : cats.map(_cap).join(', '),
            on: cats.isNotEmpty,
            onTap: () => _pickMany(
              'Category',
              [for (final (v, l) in _cats) (v, l, null)],
              cats,
              (s) => setState(() => cats = s),
            ),
          ),
          _FilterButton(
            key: const Key('filter-kind'),
            label: kinds.isEmpty
                ? 'Kind'
                : [
                    for (final (k, l) in _kinds)
                      if (kinds.contains(k)) l,
                  ].join(', '),
            on: kinds.isNotEmpty,
            onTap: () =>
                _pickMany('Kind', [for (final (k, l) in _kinds) (k, l, null)], kinds, (s) => setState(() => kinds = s)),
          ),
          _FilterButton(
            key: const Key('filter-game'),
            label: gameName ?? 'Any game',
            on: game != null,
            onTap: () => _pickOne(
              'Game',
              [
                (null, 'Any game', 'Every move in the database'),
                for (final g in games)
                  (g.id, g.name, 'Generation ${_roman[g.generation.clamp(0, 9)]} · ${g.moveIds.length} moves'),
              ],
              game,
              (v) => setState(() => game = v),
            ),
          ),
        ],
      ),
      const SizedBox(height: 8),
      _sortRow<MoveSort>(
        key: 'move-sort',
        value: moveSort,
        asc: moveAsc,
        options: const [
          (MoveSort.power, 'Power'),
          (MoveSort.pp, 'PP'),
          (MoveSort.accuracy, 'Acc'),
          (MoveSort.name, 'Name'),
        ],
        onSort: (s) => setState(() {
          // Another column starts in its natural order: names A→Z, numbers high→low.
          if (s == moveSort) {
            moveAsc = !moveAsc;
          } else {
            moveSort = s;
            moveAsc = s == MoveSort.name;
          }
        }),
      ),
    ];
  }

  List<Widget> _itemFilters(List<ItemOut> all) {
    final cats = itemCategories(all);
    return [
      Wrap(
        spacing: 6,
        runSpacing: 6,
        children: [
          _FilterButton(
            key: const Key('filter-item-category'),
            label: itemCats.isEmpty ? 'Category' : itemCats.map(_cap).join(', '),
            on: itemCats.isNotEmpty,
            onTap: () => _pickMany(
              'Category',
              [for (final (c, n) in cats) (c, _cap(c), '$n items')],
              itemCats,
              (s) => setState(() => itemCats = s),
            ),
          ),
        ],
      ),
      const SizedBox(height: 8),
      _sortRow<ItemSort>(
        key: 'item-sort',
        value: itemSort,
        asc: itemAsc,
        options: const [(ItemSort.name, 'Name'), (ItemSort.cost, 'Cost'), (ItemSort.fling, 'Fling')],
        onSort: (s) => setState(() {
          if (s == itemSort) {
            itemAsc = !itemAsc;
          } else {
            itemSort = s;
            itemAsc = s == ItemSort.name;
          }
        }),
      ),
    ];
  }

  /// Sort keys as a segmented control; tapping the current key flips the direction.
  Widget _sortRow<S>({
    required String key,
    required S value,
    required bool asc,
    required List<(S, String)> options,
    required ValueChanged<S> onSort,
  }) => Row(
    children: [
      Text('Sort', style: AppText.label.copyWith(color: Palette.mutedSlate)),
      const SizedBox(width: 8),
      Expanded(
        child: Segmented<S>(
          key: Key(key),
          compact: true,
          value: value,
          onChanged: onSort,
          options: [for (final (s, l) in options) (s, s == value ? '$l ${asc ? '↑' : '↓'}' : l, Key('$key-$l'))],
        ),
      ),
    ],
  );

  // ------------------------------------------------------------------ results

  Widget _results<T>(AsyncValue<List<T>> v, Widget Function(List<T>) list) => switch (v) {
    AsyncData(:final value) => list(value),
    AsyncError(:final error) when error is Unreachable => CantReach(address: error.address, onRetry: _retry),
    AsyncError() => Center(
      child: TextButton(onPressed: _retry, child: const Text("Couldn't load the catalog. Tap to retry.")),
    ),
    _ => const Center(child: CircularProgressIndicator()),
  };

  void _retry() => switch (kind) {
    FinderKind.moves => ref.invalidate(allMovesProvider),
    FinderKind.abilities => ref.invalidate(allAbilitiesProvider),
    FinderKind.items => ref.invalidate(allItemsProvider),
  };

  Widget _summary(int shown, int total, String noun) => Padding(
    padding: const EdgeInsets.fromLTRB(Space.gutter + 2, Space.sm, Space.gutter, 4),
    // A fixed height, so the row doesn't jump when Clear appears.
    child: SizedBox(
      height: 40,
      child: Row(
        children: [
          Expanded(
            child: Text(
              '${_count(shown)} of ${_count(total)} $noun',
              key: const Key('finder-count'),
              style: AppText.bodySmall.copyWith(color: Palette.mutedSlate),
            ),
          ),
          if (_filtered) TextButton(key: const Key('finder-clear'), onPressed: _clear, child: const Text('Clear')),
        ],
      ),
    ),
  );

  Widget _list(int count, Widget Function(int) row) => count == 0
      ? Center(
          child: Text('Nothing matches.', style: AppText.body.copyWith(color: Palette.mutedSlate)),
        )
      : ListView.separated(
          padding: const EdgeInsets.fromLTRB(Space.gutter, 0, Space.gutter, Space.gutter * 2),
          itemCount: count,
          separatorBuilder: (_, _) => const Divider(height: 1, thickness: 1, color: Palette.hairlineSoft),
          itemBuilder: (_, i) => row(i),
        );

  Widget _moveList(List<FinderMove> all) {
    final inGame = game == null
        ? null
        : ref.watch(moveGamesProvider).value?.where((g) => g.id == game).firstOrNull?.moveIds.toSet();
    final rows = filterMoves(
      all,
      query: q,
      types: types,
      categories: cats,
      kinds: kinds,
      inGame: inGame,
      sort: moveSort,
      ascending: moveAsc,
    );
    String n(int? v) => v?.toString() ?? '—';
    return Column(
      children: [
        _summary(rows.length, all.length, 'moves'),
        Expanded(
          child: _list(rows.length, (i) {
            final f = rows[i];
            final m = f.move;
            return InkWell(
              key: Key('finder-move-${m.id}'),
              onTap: () => openMove(context, m),
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 10),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(m.name, style: AppText.title.copyWith(fontSize: 15)),
                          const SizedBox(height: 3),
                          Wrap(
                            spacing: 6,
                            runSpacing: 4,
                            crossAxisAlignment: WrapCrossAlignment.center,
                            children: [
                              if (m.type != null) TypeChip(m.type!, dense: true),
                              Text(
                                [
                                  f.classes.map(_cap).join(' / '),
                                  if (m.kind != MoveOutKind.regular) m.kind == MoveOutKind.z ? 'Z-Move' : 'Max Move',
                                ].where((s) => s.isNotEmpty).join(' · '),
                                style: AppText.bodySmall.copyWith(color: Palette.mutedSlate),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    _num(n(m.power), 'Pow'),
                    _num(n(m.accuracy), 'Acc'),
                    _num(n(m.pp), 'PP'),
                  ],
                ),
              ),
            );
          }),
        ),
      ],
    );
  }

  Widget _num(String v, String label) => SizedBox(
    width: 44,
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Text(v, style: AppText.readout.copyWith(fontSize: 14, color: Palette.instrumentInk)),
        Text(label, style: AppText.label.copyWith(fontSize: 10.5, color: Palette.faintSlate)),
      ],
    ),
  );

  Widget _abilityList(List<AbilityOut> all) {
    final rows = filterAbilities(all, query: q, ascending: abilityAsc);
    return Column(
      children: [
        _summary(rows.length, all.length, 'abilities'),
        Expanded(
          child: _list(rows.length, (i) {
            final a = rows[i];
            return InkWell(
              key: Key('finder-ability-${a.id}'),
              onTap: () => showLookupSheet(context, (scroll) => AbilitySheet(ability: a, scroll: scroll)),
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 10),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(a.name, style: AppText.title.copyWith(fontSize: 15)),
                    Text(
                      a.shortEffect ?? a.effect ?? '',
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: AppText.bodySmall.copyWith(color: Palette.inkDim),
                    ),
                  ],
                ),
              ),
            );
          }),
        ),
      ],
    );
  }

  Widget _itemList(List<ItemOut> all) {
    final rows = filterItems(all, query: q, categories: itemCats, sort: itemSort, ascending: itemAsc);
    return Column(
      children: [
        _summary(rows.length, all.length, 'items'),
        Expanded(
          child: _list(rows.length, (i) {
            final it = rows[i];
            return InkWell(
              key: Key('finder-item-${it.id}'),
              onTap: () => showLookupSheet(context, (scroll) => ItemSheet(item: it, scroll: scroll)),
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 10),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(it.name, style: AppText.title.copyWith(fontSize: 15)),
                          Text(
                            [if (it.category != null) _cap(it.category!), ?it.shortEffect].join(' · '),
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: AppText.bodySmall.copyWith(color: Palette.inkDim),
                          ),
                        ],
                      ),
                    ),
                    _num(it.cost == null || it.cost == 0 ? '—' : '${it.cost}', 'Cost'),
                    _num(it.flingPower == null || it.flingPower == 0 ? '—' : '${it.flingPower}', 'Fling'),
                  ],
                ),
              ),
            );
          }),
        ),
      ],
    );
  }

  // ------------------------------------------------------------------ pickers

  Future<void> _pickMany<T>(
    String title,
    List<(T, String, String?)> options,
    Set<T> current,
    ValueChanged<Set<T>> apply,
  ) => showModalBottomSheet<void>(
    context: context,
    useRootNavigator: true,
    showDragHandle: true,
    isScrollControlled: true,
    builder: (sheet) => StatefulBuilder(
      builder: (context, setLocal) {
        var picked = {...current};
        return StatefulBuilder(
          builder: (context, setSheet) {
            return _PickerSheet(
              title: title,
              children: [
                for (final (v, l, hint) in options)
                  CheckboxListTile(
                    key: Key('pick-$l'),
                    value: picked.contains(v),
                    title: Text(l, style: AppText.body),
                    subtitle: hint == null
                        ? null
                        : Text(hint, style: AppText.bodySmall.copyWith(color: Palette.mutedSlate)),
                    controlAffinity: ListTileControlAffinity.leading,
                    onChanged: (on) {
                      setSheet(() => picked = on == true ? {...picked, v} : ({...picked}..remove(v)));
                      apply(picked);
                    },
                  ),
              ],
            );
          },
        );
      },
    ),
  );

  Future<void> _pickOne<T>(String title, List<(T, String, String?)> options, T current, ValueChanged<T> apply) =>
      showModalBottomSheet<void>(
        context: context,
        useRootNavigator: true,
        showDragHandle: true,
        isScrollControlled: true,
        builder: (sheet) => _PickerSheet(
          title: title,
          children: [
            for (final (v, l, hint) in options)
              ListTile(
                key: Key('pick-$l'),
                selected: v == current,
                selectedColor: Palette.instrumentInk,
                leading: Icon(
                  v == current ? Icons.radio_button_checked : Icons.radio_button_unchecked,
                  color: v == current ? Palette.pokeballRed : Palette.faintSlate,
                ),
                title: Text(l, style: AppText.body),
                subtitle: hint == null
                    ? null
                    : Text(hint, style: AppText.bodySmall.copyWith(color: Palette.mutedSlate)),
                onTap: () {
                  apply(v);
                  Navigator.of(sheet).pop();
                },
              ),
          ],
        ),
      );
}

class _PickerSheet extends StatelessWidget {
  const _PickerSheet({required this.title, required this.children});

  final String title;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) => ConstrainedBox(
    constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * .75),
    child: SafeArea(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(Space.gutter, 0, Space.gutter, Space.xs),
            child: Text(title, style: AppText.headline),
          ),
          Flexible(child: ListView(shrinkWrap: true, children: children)),
        ],
      ),
    ),
  );
}

/// A filter control: white and hairline when off, ink-filled when it holds a choice.
class _FilterButton extends StatelessWidget {
  const _FilterButton({super.key, required this.label, required this.on, required this.onTap});

  final String label;
  final bool on;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Material(
    color: on ? Palette.instrumentInk : Palette.panelWhite,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(Radii.control),
      side: BorderSide(color: on ? Palette.instrumentInk : Palette.hairline),
    ),
    child: InkWell(
      borderRadius: BorderRadius.circular(Radii.control),
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 200),
              child: Text(
                label,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: AppText.label.copyWith(fontSize: 13.5, color: on ? Palette.panelWhite : Palette.inkDim),
              ),
            ),
            const SizedBox(width: 4),
            Icon(Icons.expand_more, size: 16, color: on ? Palette.panelWhite : Palette.mutedSlate),
          ],
        ),
      ),
    ),
  );
}
