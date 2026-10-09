import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/export.dart';
import '../../data/pokedex_repository.dart';
import '../../data/server.dart';
import '../../data/sprites.dart';
import '../../theme/theme.dart';
import '../../theme/tokens.g.dart';
import '../../widgets/artwork.dart';
import '../../widgets/type_chip.dart';

/// Opens a search over the Pokédex (forms included) and returns the pick.
Future<PokemonSummary?> pickPokemon(BuildContext context) => showModalBottomSheet<PokemonSummary>(
      context: context,
      useRootNavigator: true, // over the tab bar
      isScrollControlled: true,
      showDragHandle: true,
      backgroundColor: Palette.panelWhite,
      builder: (_) => const FractionallySizedBox(heightFactor: 0.9, child: PokemonPicker()),
    );

class PokemonPicker extends ConsumerStatefulWidget {
  const PokemonPicker({super.key});

  @override
  ConsumerState<PokemonPicker> createState() => _PokemonPickerState();
}

class _PokemonPickerState extends ConsumerState<PokemonPicker> {
  Timer? _debounce;
  String _q = '';
  Future<ResultPage>? _results;

  @override
  void initState() {
    super.initState();
    _results = ref.read(repositoryProvider).page(const ListQuery());
  }

  @override
  void dispose() {
    _debounce?.cancel();
    super.dispose();
  }

  void _search(String text) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 250), () {
      if (text.trim() == _q) return;
      setState(() {
        _q = text.trim();
        _results = ref.read(repositoryProvider).page(ListQuery(q: _q));
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    final base = ref.watch(serverAddressProvider);
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: Space.gutter),
      child: Column(children: [
        TextField(
          key: const Key('picker-search'),
          autofocus: true,
          autocorrect: false,
          onChanged: _search,
          decoration: const InputDecoration(prefixIcon: Icon(Icons.search), hintText: 'Name or dex number', isDense: true),
        ),
        const SizedBox(height: Space.sm),
        Expanded(
          child: FutureBuilder<ResultPage>(
            future: _results,
            builder: (context, snap) {
              if (snap.hasError) return Center(child: Text("Couldn't search: ${snap.error}", style: AppText.bodySmall));
              final items = snap.data?.items;
              if (items == null) return const Center(child: CircularProgressIndicator());
              if (items.isEmpty) return Center(child: Text('No Pokémon match.', style: AppText.body));
              return ListView.builder(
                itemCount: items.length,
                itemBuilder: (context, i) {
                  final p = items[i];
                  return ListTile(
                    key: Key('pick-${p.id}-${p.formId}'),
                    contentPadding: EdgeInsets.zero,
                    leading: Artwork(thumbUrl(base, p.spriteUrl), size: 40),
                    title: Text(p.name, style: AppText.title),
                    subtitle: Wrap(spacing: 4, children: [for (final t in p.types) TypeChip(t, dense: true)]),
                    trailing: Text('#${p.dexNumber.toString().padLeft(3, '0')}', style: AppText.readout),
                    onTap: () => Navigator.pop(context, p),
                  );
                },
              );
            },
          ),
        ),
      ]),
    );
  }
}
