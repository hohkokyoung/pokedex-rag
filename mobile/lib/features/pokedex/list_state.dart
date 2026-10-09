import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/export.dart';
import '../../data/pokedex_repository.dart';
import '../../data/server.dart';

/// What the list is showing for (search, filters, sort). Changing it reloads from page 1.
final listQueryProvider = NotifierProvider<ListQueryNotifier, ListQuery>(ListQueryNotifier.new);

class ListQueryNotifier extends Notifier<ListQuery> {
  @override
  ListQuery build() => const ListQuery();

  void set(ListQuery q) => state = q;
  void clearFilters() => state = ListQuery(sort: state.sort, descending: state.descending);
}

class ListState {
  const ListState({required this.items, required this.total, required this.done, this.loadingMore = false, this.moreFailed});

  final List<PokemonSummary> items;
  final int total;
  final bool done;
  final bool loadingMore;

  /// A later page failed; the rows already loaded stay and the end of the list offers a retry.
  final Object? moreFailed;
}

final pokedexListProvider = AsyncNotifierProvider<PokedexList, ListState>(PokedexList.new);

class PokedexList extends AsyncNotifier<ListState> {
  late Pager _pager;

  @override
  Future<ListState> build() async {
    _pager = Pager(ref.watch(repositoryProvider), ref.watch(listQueryProvider));
    await _pager.loadMore();
    return _snapshot();
  }

  /// Appends the next page; called as the user nears the end of the list.
  Future<void> loadMore() async {
    final current = state.value;
    if (current == null || current.done || current.loadingMore) return;
    final pager = _pager;
    state = AsyncData(_snapshot(loadingMore: true));
    try {
      await pager.loadMore();
      if (identical(pager, _pager)) state = AsyncData(_snapshot());
    } catch (e) {
      if (identical(pager, _pager)) state = AsyncData(_snapshot(moreFailed: e));
    }
  }

  ListState _snapshot({bool loadingMore = false, Object? moreFailed}) => ListState(
        items: List.unmodifiable(_pager.items),
        total: _pager.total ?? 0,
        done: _pager.done,
        loadingMore: loadingMore,
        moreFailed: moreFailed,
      );
}

/// Filter options from the backend (types without non-battle ones, generations).
final typeOptionsProvider = FutureProvider<List<String>>((ref) async {
  final chart = await ref.watch(repositoryProvider).typeChart();
  return chart.order;
});

final generationOptionsProvider = FutureProvider<List<GenerationOut>>((ref) => ref.watch(repositoryProvider).generations());
