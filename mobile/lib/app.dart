import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'features/pokedex/detail_screen.dart';
import 'features/pokedex/list_screen.dart';
import 'features/settings/settings_screen.dart';
import 'theme/theme.dart';

GoRouter buildRouter() => GoRouter(routes: [
      GoRoute(path: '/', builder: (_, _) => const ListScreen()),
      GoRoute(
        path: '/pokemon/:id',
        builder: (_, s) => DetailScreen(
          id: s.pathParameters['id']!,
          formId: int.tryParse(s.uri.queryParameters['form'] ?? ''),
        ),
      ),
      GoRoute(path: '/settings', builder: (_, _) => const SettingsScreen()),
    ]);

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
