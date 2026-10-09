import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/export.dart';
import '../../data/server.dart';

/// One Pokémon's detail, by dex number (or name).
final detailProvider = FutureProvider.family<PokemonDetail, String>(
  (ref, id) => ref.watch(repositoryProvider).detail(id),
);

/// The served type chart, kept for the session (the repository fetches it once).
final typeChartProvider = FutureProvider<TypeChartOut>((ref) => ref.watch(repositoryProvider).typeChart());
