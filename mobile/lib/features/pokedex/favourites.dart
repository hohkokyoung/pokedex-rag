import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../api/export.dart';
import '../../data/errors.dart';
import '../../data/server.dart';
import '../../data/sprites.dart';
import '../../theme/theme.dart';
import '../../theme/tokens.g.dart';
import '../../widgets/ui.dart';
import '../../widgets/artwork.dart';
import '../../widgets/cant_reach.dart';
import '../../widgets/type_chip.dart';

/// The server profile's favourites (shared with the website and Ask's "for you" picks).
final favouritesProvider = AsyncNotifierProvider<Favourites, List<FavoriteOut>>(Favourites.new);

class Favourites extends AsyncNotifier<List<FavoriteOut>> {
  @override
  Future<List<FavoriteOut>> build() async => (await ref.watch(repositoryProvider).profile()).favorites;

  bool contains(int pokemonId) => state.value?.any((f) => f.id == pokemonId) ?? false;

  /// Flips a favourite at once and reverts if the server refuses. Returns false on failure.
  Future<bool> toggle(PokemonDetail p) async {
    final before = state.value ?? const <FavoriteOut>[];
    final adding = !before.any((f) => f.id == p.id);
    state = AsyncData(adding
        ? [...before, FavoriteOut(id: p.id, dexNumber: p.dexNumber, name: p.name, types: p.types, spriteUrl: p.spriteUrl)]
        : before.where((f) => f.id != p.id).toList());
    final repo = ref.read(repositoryProvider);
    try {
      final profile = adding ? await repo.addFavourite(p.id) : await repo.removeFavourite(p.id);
      state = AsyncData(profile.favorites);
      return true;
    } catch (_) {
      state = AsyncData(before);
      return false;
    }
  }
}

class FavouriteButton extends ConsumerWidget {
  const FavouriteButton({super.key, required this.pokemon});

  final PokemonDetail pokemon;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.watch(favouritesProvider);
    final on = ref.read(favouritesProvider.notifier).contains(pokemon.id);
    return SquareButton(
      key: const Key('favourite'),
      tooltip: on ? 'Remove from favourites' : 'Add to favourites',
      icon: on ? Icons.favorite : Icons.favorite_border,
      color: on ? Palette.pokeballRed : null,
      onPressed: () async {
        final ok = await ref.read(favouritesProvider.notifier).toggle(pokemon);
        if (!ok && context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text("Couldn't update favourites. The server didn't answer.")),
          );
        }
      },
    );
  }
}

class FavouritesScreen extends ConsumerWidget {
  const FavouritesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final favs = ref.watch(favouritesProvider);
    final base = ref.watch(serverAddressProvider);
    return Scaffold(
      appBar: pageBar('Favourites'),
      body: switch (favs) {
        AsyncData(:final value) when value.isEmpty => Center(
            child: Padding(
              padding: const EdgeInsets.all(Space.gutter * 2),
              child: Text('No favourites yet. Tap the heart on a Pokémon to add it.', style: AppText.body, textAlign: TextAlign.center),
            ),
          ),
        AsyncData(:final value) => ListView.separated(
            padding: const EdgeInsets.all(Space.gutter),
            itemCount: value.length,
            separatorBuilder: (_, _) => const SizedBox(height: Space.xs),
            itemBuilder: (context, i) {
              final f = value[i];
              return Card(
                child: ListTile(
                  leading: Artwork(thumbUrl(base, f.spriteUrl), size: 44),
                  title: Text(f.name, style: AppText.title),
                  subtitle: Wrap(spacing: 4, children: [for (final t in f.types) TypeChip(t, dense: true)]),
                  trailing: Text('#${f.dexNumber.toString().padLeft(3, '0')}', style: AppText.readout),
                  onTap: () => context.push('/pokemon/${f.dexNumber}'),
                ),
              );
            },
          ),
        AsyncError(:final error) when error is Unreachable =>
          CantReach(address: error.address, onRetry: () => ref.invalidate(favouritesProvider)),
        AsyncError() => Center(child: Text('The server had a problem loading favourites.', style: AppText.body)),
        _ => const Center(child: CircularProgressIndicator()),
      },
    );
  }
}
