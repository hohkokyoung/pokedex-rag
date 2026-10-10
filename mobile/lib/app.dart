import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';

import 'widgets/ui.dart';
import 'features/tools/calc_screen.dart';
import 'features/tools/catch_screen.dart';
import 'features/tools/lookup_screen.dart';
import 'features/tools/nature_screen.dart';
import 'features/tools/tools_screen.dart';
import 'features/tools/type_calc_screen.dart';
import 'features/ask/ask_screen.dart';
import 'features/pokedex/detail_screen.dart';
import 'features/pokedex/favourites.dart';
import 'features/pokedex/list_screen.dart';
import 'features/settings/settings_screen.dart';
import 'features/teams/set_editor.dart';
import 'features/teams/team_screen.dart';
import 'features/teams/teams_screen.dart';
import 'theme/theme.dart';

/// Tabs (each keeps its own stack) plus full-screen routes that open over any tab.
GoRouter buildRouter() => GoRouter(
  routes: [
    StatefulShellRoute.indexedStack(
      builder: (_, _, shell) => AppShell(shell: shell),
      branches: [
        StatefulShellBranch(
          routes: [GoRoute(path: '/', builder: (_, _) => const ListScreen())],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/teams',
              builder: (_, _) => const TeamsScreen(),
              routes: [
                GoRoute(
                  path: ':id',
                  builder: (_, s) =>
                      TeamScreen(id: int.parse(s.pathParameters['id']!), opponentId: int.tryParse(s.uri.queryParameters['vs'] ?? '')),
                ),
              ],
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [GoRoute(path: '/ask', builder: (_, _) => const AskScreen())],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/tools',
              builder: (_, _) => const ToolsScreen(),
              routes: [
                GoRoute(path: 'calc', builder: (_, _) => const CalcScreen()),
                GoRoute(path: 'types', builder: (_, _) => const TypeCalcScreen()),
                GoRoute(path: 'natures', builder: (_, _) => const NatureScreen()),
                GoRoute(path: 'catch', builder: (_, _) => const CatchScreen()),
                GoRoute(path: 'lookup', builder: (_, _) => const LookupScreen()),
              ],
            ),
          ],
        ),
      ],
    ),
    GoRoute(
      path: '/pokemon/:id',
      builder: (_, s) => DetailScreen(id: s.pathParameters['id']!, formId: int.tryParse(s.uri.queryParameters['form'] ?? '')),
    ),
    GoRoute(
      path: '/teams/:id/slot/:slot',
      builder: (_, s) => SetEditor(teamId: int.parse(s.pathParameters['id']!), slot: int.parse(s.pathParameters['slot']!)),
    ),
    GoRoute(path: '/settings', builder: (_, _) => const SettingsScreen()),
    GoRoute(path: '/favourites', builder: (_, _) => const FavouritesScreen()),
  ],
);

class AppShell extends StatelessWidget {
  const AppShell({super.key, required this.shell});

  final StatefulNavigationShell shell;

  @override
  Widget build(BuildContext context) => Scaffold(
    body: shell,
    // The website's Tray as a tab bar, with Ask as the one red action beside it.
    bottomNavigationBar: TrayBar(
      current: shell.currentIndex,
      // Tapping the current tab returns to its first page.
      onTap: (i) => shell.goBranch(i, initialLocation: i == shell.currentIndex),
      tabs: const [
        (0, 'Pokédex', Icons.catching_pokemon, Key('tab-pokedex')),
        (1, 'Teams', Icons.groups_outlined, Key('tab-teams')),
        (3, 'Tools', Icons.tune, Key('tab-tools')),
      ],
      ask: (2, const Key('tab-ask')),
    ),
  );
}

class PokeragApp extends StatefulWidget {
  const PokeragApp({super.key});

  @override
  State<PokeragApp> createState() => _PokeragAppState();
}

class _PokeragAppState extends State<PokeragApp> {
  final _router = buildRouter();

  @override
  Widget build(BuildContext context) => MaterialApp.router(
    title: 'pokérag',
    debugShowCheckedModeBanner: false,
    theme: AppTheme.light(),
    routerConfig: _router,
    // The website's ground behind every route; screens are transparent over it.
    builder: (context, child) => AnnotatedRegion<SystemUiOverlayStyle>(
      // Dark status-bar icons and time on the light ground.
      value: SystemUiOverlayStyle.dark,
      child: Ground(child: child ?? const SizedBox.shrink()),
    ),
  );
}
