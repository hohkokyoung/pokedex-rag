import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../theme/theme.dart';
import '../../theme/tokens.g.dart';

/// The website home page's reference tools, one row each.
const tools = [
  ('types', Icons.shield_outlined, 'Type calculator', 'What a 1–2 type combination takes, resists and hits'),
  ('natures', Icons.grid_view, 'Nature helper', 'The 5×5 grid and each nature’s ±10%'),
  ('catch', Icons.catching_pokemon, 'Catch rate', 'The best balls for a wild Pokémon and situation'),
  ('lookup', Icons.search, 'Lookup', 'Moves, abilities and items'),
];

class ToolsScreen extends StatelessWidget {
  const ToolsScreen({super.key});

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: Text('Tools', style: AppText.display.copyWith(fontSize: 26))),
        body: ListView(
          padding: const EdgeInsets.fromLTRB(Space.gutter, 0, Space.gutter, Space.gutter * 2),
          children: [
            for (final (path, icon, title, sub) in tools)
              Card(
                key: Key('tool-$path'),
                child: ListTile(
                  leading: Icon(icon, color: Palette.pokeballRed),
                  title: Text(title, style: AppText.title),
                  subtitle: Text(sub, style: AppText.bodySmall.copyWith(color: Palette.inkDim)),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => context.go('/tools/$path'),
                ),
              ),
          ],
        ),
      );
}
