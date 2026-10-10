import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../theme/theme.dart';
import '../../theme/tokens.g.dart';
import '../../widgets/ui.dart';

/// The website home page's reference tools, one row each.
const tools = [
  ('calc', Icons.bolt, 'Damage calc', 'Both sides, the field, and the turn played out'),
  ('types', Icons.shield_outlined, 'Type calculator', 'What a 1–2 type combination takes, resists and hits'),
  ('natures', Icons.grid_view, 'Nature helper', 'The 5×5 grid and each nature’s ±10%'),
  ('catch', Icons.catching_pokemon, 'Catch rate', 'The best balls for a wild Pokémon and situation'),
  ('lookup', Icons.search, 'Lookup', 'Moves, abilities and items'),
];

class ToolsScreen extends StatelessWidget {
  const ToolsScreen({super.key});

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: pageBar('Tools', root: true),
        body: ListView(
          padding: const EdgeInsets.fromLTRB(Space.gutter, Space.xs, Space.gutter, Space.gutter * 2),
          children: [
            // One grouped panel, rows split by hairlines; ink icons (red is only for actions).
            Card(
              clipBehavior: Clip.antiAlias,
              child: Column(children: [
                for (final (i, (path, icon, title, sub)) in tools.indexed) ...[
                  if (i > 0) const Divider(height: 1, thickness: 1, indent: 64, color: Palette.hairlineSoft),
                  InkWell(
                    key: Key('tool-$path'),
                    onTap: () => context.go('/tools/$path'),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: Space.md, vertical: 12),
                      child: Row(children: [
                        Container(
                          width: 38,
                          height: 38,
                          decoration: BoxDecoration(color: Palette.insetGray, borderRadius: BorderRadius.circular(Radii.control)),
                          child: Icon(icon, size: 20, color: Palette.instrumentInk),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                            Text(title, style: AppText.title),
                            const SizedBox(height: 2),
                            Text(sub, style: AppText.bodySmall.copyWith(color: Palette.mutedSlate)),
                          ]),
                        ),
                        const Icon(Icons.chevron_right, color: Palette.faintSlate),
                      ]),
                    ),
                  ),
                ],
              ]),
            ),
          ],
        ),
      );
}
