import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../api/export.dart';
import '../../data/errors.dart';
import '../../data/server.dart';
import '../../data/sprites.dart';
import '../../theme/theme.dart';
import '../../theme/tokens.g.dart';
import '../../widgets/artwork.dart';
import '../../widgets/cant_reach.dart';
import '../../widgets/grade.dart';
import '../../widgets/type_chip.dart';
import 'team_state.dart';

/// Every saved team, rated as on the website's /teams.
class TeamsScreen extends ConsumerWidget {
  const TeamsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final teams = ref.watch(teamsListProvider);
    return Scaffold(
      appBar: AppBar(
        title: Text('Teams', style: AppText.display.copyWith(fontSize: 26)),
        actions: [
          IconButton(
            key: const Key('new-team'),
            tooltip: 'New team',
            icon: const Icon(Icons.add),
            onPressed: () => createTeam(context, ref),
          ),
        ],
      ),
      body: switch (teams) {
        AsyncData(:final value) when value.isEmpty => Center(
            child: Padding(
              padding: const EdgeInsets.all(Space.gutter * 2),
              child: Text('No teams yet. Tap + to build one.', style: AppText.body, textAlign: TextAlign.center),
            ),
          ),
        AsyncData(:final value) => RefreshIndicator(
            onRefresh: () async => ref.invalidate(teamsListProvider),
            child: ListView.separated(
              padding: const EdgeInsets.fromLTRB(Space.gutter, Space.xs, Space.gutter, Space.gutter * 2),
              itemCount: value.length,
              separatorBuilder: (_, _) => const SizedBox(height: Space.md),
              itemBuilder: (_, i) => TeamCard(team: value[i]),
            ),
          ),
        AsyncError(:final error) when error is Unreachable =>
          CantReach(address: error.address, onRetry: () => ref.invalidate(teamsListProvider)),
        AsyncError() => Center(child: Text('The server had a problem loading teams.', style: AppText.body)),
        _ => const Center(child: CircularProgressIndicator()),
      },
    );
  }
}

/// Asks for a name, creates the team on the server and opens it.
Future<void> createTeam(BuildContext context, WidgetRef ref) async {
  final name = await showDialog<String>(context: context, builder: (_) => const _NameDialog(title: 'New team', action: 'Create'));
  if (name == null || name.trim().isEmpty || !context.mounted) return;
  try {
    final team = await ref.read(teamsRepositoryProvider).create(name.trim());
    ref.invalidate(teamsListProvider);
    if (context.mounted) context.push('/teams/${team.id}');
  } catch (e) {
    if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Couldn't create the team: $e")));
  }
}

class _NameDialog extends StatefulWidget {
  const _NameDialog({required this.title, required this.action, this.initial = ''});

  final String title;
  final String action;
  final String initial;

  @override
  State<_NameDialog> createState() => _NameDialogState();
}

class _NameDialogState extends State<_NameDialog> {
  late final _c = TextEditingController(text: widget.initial);

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
        title: Text(widget.title),
        content: TextField(
          key: const Key('team-name'),
          controller: _c,
          autofocus: true,
          maxLength: 64,
          decoration: const InputDecoration(hintText: 'Team name'),
          onSubmitted: (v) => Navigator.pop(context, v),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          FilledButton(key: const Key('name-ok'), onPressed: () => Navigator.pop(context, _c.text), child: Text(widget.action)),
        ],
      );
}

Future<String?> askTeamName(BuildContext context, String current) =>
    showDialog<String>(context: context, builder: (_) => _NameDialog(title: 'Rename team', action: 'Rename', initial: current));

Future<bool> confirmDelete(BuildContext context, String name) async =>
    await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Delete $name?'),
        content: const Text('This removes the team from the server for the website too.'),
        actions: [
          TextButton(key: const Key('delete-cancel'), onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          FilledButton(key: const Key('delete-ok'), onPressed: () => Navigator.pop(context, true), child: const Text('Delete')),
        ],
      ),
    ) ??
    false;

class TeamCard extends ConsumerWidget {
  const TeamCard({super.key, required this.team});

  final TeamSummary team;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final base = ref.watch(serverAddressProvider);
    final analysis = team.size > 0 ? ref.watch(teamAnalysisProvider((team.id, null))).value : null;
    final strategy = team.size > 0 ? ref.watch(teamStrategyProvider(team.id)).value : null;
    final summary = team.size > 0 ? ref.watch(teamSummaryProvider(team.id)).value : null;
    final rating = analysis?.rating;
    final profile = analysis?.profile;
    return Card(
      key: Key('team-card-${team.id}'),
      child: InkWell(
        borderRadius: BorderRadius.circular(Radii.card),
        onTap: () => context.push('/teams/${team.id}'),
        child: Padding(
          padding: const EdgeInsets.all(Space.md),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              if (rating != null) ...[GradeBadge(rating.grade.json ?? '?'), const SizedBox(width: Space.sm)],
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(team.name, style: AppText.title, overflow: TextOverflow.ellipsis),
                  if (rating != null)
                    Text('${rating.overall}/100 · ${strategy?.style ?? profile?.style ?? ''}',
                        style: AppText.readout.copyWith(color: Palette.inkDim)),
                ]),
              ),
              PopupMenuButton<String>(
                key: Key('team-menu-${team.id}'),
                onSelected: (_) async {
                  if (!await confirmDelete(context, team.name)) return;
                  try {
                    await ref.read(teamsRepositoryProvider).delete(team.id);
                  } catch (e) {
                    if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Couldn't delete: $e")));
                  }
                  ref.invalidate(teamsListProvider);
                },
                itemBuilder: (_) => [const PopupMenuItem(key: Key('team-delete'), value: 'delete', child: Text('Delete'))],
              ),
            ]),
            const SizedBox(height: Space.sm),
            if (team.size == 0)
              Text('Empty: tap to add Pokémon.', style: AppText.bodySmall.copyWith(color: Palette.mutedSlate))
            else ...[
              Row(children: [for (final s in team.sprites) Artwork(thumbUrl(base, s), size: 40)]),
              if (summary != null) ...[
                const SizedBox(height: Space.xs),
                Text(summary.text, maxLines: 3, overflow: TextOverflow.ellipsis, style: AppText.bodySmall.copyWith(color: Palette.inkDim)),
              ],
              if (profile != null) ...[
                const SizedBox(height: Space.sm),
                _facts('Weak to', profile.weakTo.take(4).map((w) => w.type).toList(), ok: 'No weaknesses'),
                _facts('Resists', profile.resists.take(4).map((w) => w.type).toList(), ok: 'Nothing'),
                Text('Hits ${profile.strongVs.length}/18 types hard', style: AppText.bodySmall),
              ],
              if (rating != null) ...[
                const SizedBox(height: Space.sm),
                Wrap(spacing: 6, runSpacing: 6, children: [
                  for (final a in rating.areas)
                    Row(mainAxisSize: MainAxisSize.min, children: [
                      Text(a.label, style: AppText.bodySmall.copyWith(color: Palette.mutedSlate)),
                      const SizedBox(width: 4),
                      Text(a.grade.json ?? '', style: AppText.readout.copyWith(color: gradeTextColor(a.grade.json ?? ''))),
                    ]),
                ]),
                ..._fixes(rating),
              ],
            ],
          ]),
        ),
      ),
    );
  }

  /// The weakest grades' fixes, worst first (up to three, as on the website's cards).
  List<Widget> _fixes(TeamRating r) {
    final gaps = r.areas.where((a) => a.fix != null).toList()..sort((x, y) => x.score.compareTo(y.score));
    return [
      for (final a in gaps.take(3))
        Padding(
          padding: const EdgeInsets.only(top: Space.xs),
          child: Text('${a.label}: ${a.fix}', style: AppText.bodySmall.copyWith(color: gradeTextColor(a.grade.json ?? ''))),
        ),
    ];
  }

  Widget _facts(String label, List<String> types, {required String ok}) => Padding(
        padding: const EdgeInsets.only(bottom: 4),
        child: Row(children: [
          SizedBox(width: 64, child: Text(label, style: AppText.bodySmall.copyWith(color: Palette.mutedSlate))),
          Expanded(
            child: types.isEmpty
                ? Text(ok, style: AppText.bodySmall)
                : Wrap(spacing: 4, runSpacing: 4, children: [for (final t in types) TypeChip(t, dense: true)]),
          ),
        ]),
      );
}
