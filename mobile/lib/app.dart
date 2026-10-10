import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

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
GoRouter buildRouter() => GoRouter(routes: [
      StatefulShellRoute.indexedStack(
        builder: (_, _, shell) => AppShell(shell: shell),
        branches: [
          StatefulShellBranch(routes: [GoRoute(path: '/', builder: (_, _) => const ListScreen())]),
          StatefulShellBranch(routes: [
            GoRoute(
              path: '/teams',
              builder: (_, _) => const TeamsScreen(),
              routes: [
                GoRoute(
                  path: ':id',
                  builder: (_, s) => TeamScreen(
                    id: int.parse(s.pathParameters['id']!),
                    opponentId: int.tryParse(s.uri.queryParameters['vs'] ?? ''),
                  ),
                ),
              ],
            ),
          ]),
          StatefulShellBranch(routes: [GoRoute(path: '/ask', builder: (_, _) => const AskScreen())]),
          StatefulShellBranch(routes: [
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
          ]),
        ],
      ),
      GoRoute(
        path: '/pokemon/:id',
        builder: (_, s) => DetailScreen(
          id: s.pathParameters['id']!,
          formId: int.tryParse(s.uri.queryParameters['form'] ?? ''),
        ),
      ),
      GoRoute(
        path: '/teams/:id/slot/:slot',
        builder: (_, s) => SetEditor(teamId: int.parse(s.pathParameters['id']!), slot: int.parse(s.pathParameters['slot']!)),
      ),
      GoRoute(path: '/settings', builder: (_, _) => const SettingsScreen()),
      GoRoute(path: '/favourites', builder: (_, _) => const FavouritesScreen()),
    ]);

class AppShell extends StatelessWidget {
  const AppShell({super.key, required this.shell});

  final StatefulNavigationShell shell;

  @override
  Widget build(BuildContext context) => Scaffold(
        body: shell,
        bottomNavigationBar: NavigationBar(
          selectedIndex: shell.currentIndex,
          // Tapping the current tab returns to its first page.
          onDestinationSelected: (i) => shell.goBranch(i, initialLocation: i == shell.currentIndex),
          destinations: const [
            NavigationDestination(key: Key('tab-pokedex'), icon: Icon(Icons.catching_pokemon_outlined), selectedIcon: Icon(Icons.catching_pokemon), label: 'Pokédex'),
            NavigationDestination(key: Key('tab-teams'), icon: Icon(Icons.groups_outlined), selectedIcon: Icon(Icons.groups), label: 'Teams'),
            NavigationDestination(key: Key('tab-ask'), icon: Icon(Icons.chat_bubble_outline), selectedIcon: Icon(Icons.chat_bubble), label: 'Ask'),
            NavigationDestination(key: Key('tab-tools'), icon: Icon(Icons.handyman_outlined), selectedIcon: Icon(Icons.handyman), label: 'Tools'),
          ],
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
      );
}
