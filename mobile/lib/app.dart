import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';

import 'widgets/ui.dart';
import 'features/tools/calc_screen.dart';
import 'features/tools/catch_screen.dart';
import 'features/tools/finder_screen.dart';
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

/// Every page as a MaterialPage, so it slides in the iOS way on its own ground (see the
/// theme). Left to itself go_router can fall back to pages with no transition, which cut
/// in with a flash and can't be swiped back.
Page<void> _page(GoRouterState s, Widget child) => MaterialPage<void>(key: s.pageKey, name: s.name ?? s.path, child: child);

GoRoute _go(String path, Widget Function(GoRouterState s) build, {List<RouteBase> routes = const []}) =>
    GoRoute(path: path, pageBuilder: (_, s) => _page(s, build(s)), routes: routes);

/// Tabs (each keeps its own stack) plus full-screen routes that open over any tab.
GoRouter buildRouter({String? initialLocation}) => GoRouter(
  initialLocation: initialLocation,
  routes: [
    StatefulShellRoute.indexedStack(
      builder: (_, _, shell) => AppShell(shell: shell),
      branches: [
        StatefulShellBranch(routes: [_go('/', (_) => const ListScreen())]),
        StatefulShellBranch(
          routes: [
            _go(
              '/teams',
              (_) => const TeamsScreen(),
              routes: [
                _go(
                  ':id',
                  (s) => TeamScreen(id: int.parse(s.pathParameters['id']!), opponentId: int.tryParse(s.uri.queryParameters['vs'] ?? '')),
                ),
              ],
            ),
          ],
        ),
        StatefulShellBranch(routes: [_go('/ask', (_) => const AskScreen())]),
        StatefulShellBranch(
          routes: [
            _go(
              '/tools',
              (_) => const ToolsScreen(),
              routes: [
                _go('calc', (_) => const CalcScreen()),
                _go('types', (_) => const TypeCalcScreen()),
                _go('natures', (_) => const NatureScreen()),
                _go('catch', (_) => const CatchScreen()),
                // Lookup lists every move, ability and item, with filters (the website's finder).
                _go('lookup', (_) => const FinderScreen()),
              ],
            ),
          ],
        ),
      ],
    ),
    _go('/pokemon/:id', (s) => DetailScreen(id: s.pathParameters['id']!, formId: int.tryParse(s.uri.queryParameters['form'] ?? ''))),
    _go('/teams/:id/slot/:slot', (s) => SetEditor(teamId: int.parse(s.pathParameters['id']!), slot: int.parse(s.pathParameters['slot']!))),
    _go('/settings', (_) => const SettingsScreen()),
    _go('/favourites', (_) => const FavouritesScreen()),
  ],
);

class AppShell extends StatelessWidget {
  const AppShell({super.key, required this.shell});

  final StatefulNavigationShell shell;

  @override
  Widget build(BuildContext context) => Scaffold(
    body: shell,
    bottomNavigationBar: NavBar(
      current: shell.currentIndex,
      // Tapping the current tab returns to its first page.
      onTap: (i) => shell.goBranch(i, initialLocation: i == shell.currentIndex),
      tabs: const [
        (0, 'Pokédex', Icons.catching_pokemon_outlined, Icons.catching_pokemon, Key('tab-pokedex'), false),
        (1, 'Teams', Icons.groups_outlined, Icons.groups, Key('tab-teams'), false),
        (3, 'Tools', Icons.tune_outlined, Icons.tune, Key('tab-tools'), false),
        (2, 'Ask', Icons.chat_bubble_outline, Icons.chat_bubble, Key('tab-ask'), true),
      ],
    ),
  );
}

class PokeragApp extends StatefulWidget {
  const PokeragApp({super.key, this.initialLocation});

  /// Where the app opens (null: the Pokédex).
  final String? initialLocation;

  @override
  State<PokeragApp> createState() => _PokeragAppState();
}

class _PokeragAppState extends State<PokeragApp> {
  late final _router = buildRouter(initialLocation: widget.initialLocation);

  @override
  Widget build(BuildContext context) => appFor(_router);
}

/// The app around a router (the tests use it too, so they run with the real theme).
Widget appFor(GoRouter router) => MaterialApp.router(
  title: 'pokérag',
  debugShowCheckedModeBanner: false,
  theme: AppTheme.light(),
  routerConfig: router,
  // The website's ground behind the shell; each page also paints its own (see theme).
  builder: (context, child) => AnnotatedRegion<SystemUiOverlayStyle>(
    // Dark status-bar icons and time on the light ground.
    value: SystemUiOverlayStyle.dark,
    child: Ground(child: child ?? const SizedBox.shrink()),
  ),
);
