import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../api/export.dart';
import '../../data/server.dart';
import '../../theme/theme.dart';
import '../../theme/tokens.g.dart';
import '../pokedex/favourites.dart';
import '../pokedex/filters_sheet.dart' show TypeToggle;
import '../pokedex/list_state.dart' show typeOptionsProvider;

/// The server profile's preferred types (shared with the website), for "for you" answers.
final preferredTypesProvider = AsyncNotifierProvider<PreferredTypes, List<String>>(PreferredTypes.new);

class PreferredTypes extends AsyncNotifier<List<String>> {
  PokeragClient get _api => PokeragClient(ref.read(dioProvider));

  @override
  Future<List<String>> build() async {
    ref.watch(dioProvider);
    return (await _api.getProfileApiProfileGet()).preferredTypes;
  }

  Future<void> toggle(String type) async {
    final before = state.value ?? const <String>[];
    final next = before.contains(type) ? before.where((t) => t != type).toList() : [...before, type];
    state = AsyncData(next);
    try {
      final p = await _api.updateProfileApiProfilePut(body: ProfileUpdate(preferredTypes: next));
      state = AsyncData(p.preferredTypes);
    } on DioException {
      state = AsyncData(before);
    }
  }
}

Future<void> showProfileSheet(BuildContext context) => showModalBottomSheet<void>(
      context: context,
      useRootNavigator: true,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (_) => const FractionallySizedBox(heightFactor: 0.8, child: ProfileSheet()),
    );

class ProfileSheet extends ConsumerWidget {
  const ProfileSheet({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final types = ref.watch(typeOptionsProvider).value ?? const <String>[];
    final preferred = ref.watch(preferredTypesProvider).value ?? const <String>[];
    final favs = ref.watch(favouritesProvider).value ?? const <FavoriteOut>[];
    return ListView(
      padding: const EdgeInsets.fromLTRB(Space.gutter, 0, Space.gutter, Space.gutter * 2),
      children: [
        Text('Your profile', style: AppText.headline),
        Text('Only "for you" questions use this. It\'s the same profile as the website.',
            style: AppText.bodySmall.copyWith(color: Palette.mutedSlate)),
        const SizedBox(height: Space.md),
        Text('Preferred types', style: AppText.label.copyWith(color: Palette.mutedSlate)),
        const SizedBox(height: Space.xs),
        Wrap(spacing: 6, runSpacing: 6, children: [
          for (final t in types)
            TypeToggle(
              key: Key('pref-$t'),
              type: t,
              selected: preferred.contains(t),
              onChanged: (_) => ref.read(preferredTypesProvider.notifier).toggle(t),
            ),
        ]),
        const SizedBox(height: Space.lg),
        Text('Favourites (${favs.length})', style: AppText.label.copyWith(color: Palette.mutedSlate)),
        if (favs.isEmpty)
          Text('Tap the heart on a Pokémon to add it.', style: AppText.bodySmall)
        else
          for (final f in favs)
            ListTile(
              contentPadding: EdgeInsets.zero,
              dense: true,
              title: Text(f.name, style: AppText.bodySmall.copyWith(fontWeight: FontWeight.w600)),
              trailing: Text('#${f.dexNumber}', style: AppText.readout),
              onTap: () {
                Navigator.of(context).pop();
                context.push('/pokemon/${f.dexNumber}');
              },
            ),
      ],
    );
  }
}
