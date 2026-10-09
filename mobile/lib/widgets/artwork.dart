import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../theme/tokens.g.dart';

typedef ArtworkBuilder = Widget Function(String url, double size, {Duration fadeIn});

/// How artwork is drawn: cached network images in the app; tests swap in a placeholder.
final artworkProvider = Provider<ArtworkBuilder>((ref) => _network);

Widget _network(String url, double size, {Duration fadeIn = const Duration(milliseconds: 200)}) => CachedNetworkImage(
      imageUrl: url,
      width: size,
      height: size,
      fadeInDuration: fadeIn,
      errorWidget: (_, _, _) => SizedBox(
        width: size,
        height: size,
        child: Icon(Icons.catching_pokemon, size: size / 2, color: Palette.faintSlate),
      ),
    );

class Artwork extends ConsumerWidget {
  const Artwork(this.url, {super.key, required this.size});

  final String url;
  final double size;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final still = MediaQuery.disableAnimationsOf(context);
    return ref.watch(artworkProvider)(url, size, fadeIn: still ? Duration.zero : const Duration(milliseconds: 200));
  }
}
