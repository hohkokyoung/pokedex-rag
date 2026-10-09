import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/export.dart';
import '../../data/server.dart';

/// One Pokémon's detail, by dex number (or name).
final detailProvider = FutureProvider.family<PokemonDetail, String>(
  (ref, id) => ref.watch(repositoryProvider).detail(id),
);

/// The number of species, for previous / next bounds.
final dexTotalProvider = FutureProvider<int>((ref) => ref.watch(repositoryProvider).dexTotal());

/// The served type chart, kept for the session (the repository fetches it once).
final typeChartProvider = FutureProvider<TypeChartOut>((ref) => ref.watch(repositoryProvider).typeChart());

/// A Pokémon's (or form's) moves in one game; a null game means the newest.
final movesProvider = FutureProvider.family<PokemonGameMovesOut, (int, int?)>(
  (ref, k) => ref.watch(repositoryProvider).moves(k.$1, game: k.$2),
);

/// Who learns a move in one game.
final learnersProvider = FutureProvider.family<MoveGameLearnersOut, (int, int?)>(
  (ref, k) => ref.watch(repositoryProvider).learners(k.$1, game: k.$2),
);

/// Where to find a Pokémon in one game (version); null means the newest it's in.
final encountersProvider = FutureProvider.family<PokemonEncountersOut, (int, int?)>(
  (ref, k) => ref.watch(repositoryProvider).encounters(k.$1, version: k.$2),
);
