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
import '../../widgets/ui.dart';
import '../../widgets/grade.dart';
import 'coach_section.dart';
import 'coach_state.dart';
import 'pokemon_picker.dart';
import 'team_report.dart';
import 'team_state.dart';
import 'teams_screen.dart';

/// One team: its six slots, an optional opponent, and the report.
class TeamScreen extends ConsumerWidget {
  const TeamScreen({super.key, required this.id, this.opponentId});

  final int id;
  final int? opponentId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final team = ref.watch(teamProvider(id));
    // Keep this visit's coach thread while the page is open, even scrolled away.
    ref.listen(coachProvider(id), (_, _) {});
    return Scaffold(
      appBar: AppBar(
        actions: [
          if (team.value != null)
            SquareButton(
              key: const Key('rename'),
              tooltip: 'Rename',
              icon: Icons.edit_outlined,
              onPressed: () async {
                final name = await askTeamName(context, team.value!.name);
                if (name == null || name.trim().isEmpty) return;
                await ref.read(teamsRepositoryProvider).rename(id, name.trim());
                invalidateTeamW(ref, id);
              },
            ),
          const SizedBox(width: Space.gutter),
        ],
      ),
      body: switch (team) {
        AsyncData(:final value) => _Body(team: value, opponentId: opponentId),
        AsyncError(:final error) when error is Unreachable =>
          CantReach(address: error.address, onRetry: () => ref.invalidate(teamProvider(id))),
        AsyncError(:final error) when error is NotFound => Center(child: Text('This team no longer exists.', style: AppText.body)),
        AsyncError() => Center(child: Text('The server had a problem loading this team.', style: AppText.body)),
        _ => const Center(child: CircularProgressIndicator()),
      },
    );
  }
}

enum TeamPart { report, coach, compare }

/// The team's grade and slots, then Report / Coach / Compare. All three stay built while
/// hidden, so the coach's thread and its cards' Applied / Added state survive switching.
class _Body extends ConsumerStatefulWidget {
  const _Body({required this.team, required this.opponentId});

  final TeamOut team;
  final int? opponentId;

  @override
  ConsumerState<_Body> createState() => _BodyState();
}

class _BodyState extends ConsumerState<_Body> {
  late TeamPart part = widget.opponentId != null ? TeamPart.compare : TeamPart.report;

  @override
  Widget build(BuildContext context) {
    final team = widget.team;
    final opponentId = widget.opponentId;
    final rated = team.members.isEmpty ? null : ref.watch(teamAnalysisProvider((team.id, null))).value;
    Widget shown(TeamPart p, Widget child) => Visibility(visible: part == p, maintainState: true, child: child);
    return RefreshIndicator(
      onRefresh: () async => invalidateTeamW(ref, team.id),
      // Not lazy: the page is short, and the coach's thread and cards must stay built
      // (and laid out) while scrolled away.
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(Space.gutter, 0, Space.gutter, Space.gutter * 3),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          _Header(
            team: team,
            rating: rated?.rating,
            profile: rated?.profile,
            style: team.members.isEmpty ? null : ref.watch(teamStrategyProvider(team.id)).value?.style,
          ),
          const SizedBox(height: Space.md),
          GridView.count(
            crossAxisCount: 3,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 8,
            crossAxisSpacing: 8,
            childAspectRatio: 0.82,
            children: [
              for (var slot = 1; slot <= 6; slot++)
                SlotTile(
                  team: team,
                  slot: slot,
                  member: team.members.where((m) => m.slot == slot).firstOrNull,
                  role: rated?.roles.members.where((r) => r.slot == slot).firstOrNull,
                ),
            ],
          ),
          const SizedBox(height: Space.md),
          if (team.members.isEmpty) ...[
            Text('Add your first Pokémon to rate the team.', style: AppText.body.copyWith(color: Palette.inkDim)),
            const SizedBox(height: Space.md),
            CoachSection(team: team),
          ] else ...[
            Segmented<TeamPart>(
              key: const Key('team-parts'),
              value: part,
              onChanged: (p) => setState(() => part = p),
              options: const [
                (TeamPart.report, 'Report', Key('part-report')),
                (TeamPart.coach, 'Coach', Key('part-coach')),
                (TeamPart.compare, 'Compare', Key('part-compare')),
              ],
            ),
            const SizedBox(height: Space.sm),
            shown(TeamPart.report, TeamReport(team: team)),
            shown(TeamPart.coach, CoachSection(team: team, opponentId: opponentId)),
            shown(
              TeamPart.compare,
              Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                _OpponentPicker(team: team, opponentId: opponentId),
                if (opponentId != null) ...[
                  const SizedBox(height: Space.sm),
                  MatchupCard(teamId: team.id, opponentId: opponentId),
                ] else
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: Space.sm),
                    child: Text('Pick another saved team to see who is favoured, their threats and your answers.',
                        style: AppText.bodySmall.copyWith(color: Palette.mutedSlate)),
                  ),
              ]),
            ),
          ],
        ]),
      ),
    );
  }
}

/// Grade first: the badge, the name, then score, play style and lean.
class _Header extends StatelessWidget {
  const _Header({required this.team, this.rating, this.profile, this.style});

  final TeamOut team;
  final TeamRating? rating;
  final TeamProfile? profile;
  final String? style;

  @override
  Widget build(BuildContext context) {
    final r = rating;
    final gap = (r?.areas.where((x) => x.fix != null).toList() ?? [])..sort((x, y) => x.score.compareTo(y.score));
    final gapArea = gap.firstOrNull;
    return Row(children: [
      if (r != null) ...[GradeBadge(r.grade.json ?? '?', size: 56), const SizedBox(width: Space.md)],
      Expanded(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(team.name, key: const Key('team-title'), maxLines: 2, overflow: TextOverflow.ellipsis,
              style: AppText.display.copyWith(fontSize: 26, fontWeight: FontWeight.w700, height: 1.08)),
          if (r != null)
            Text.rich(
              key: const Key('rating-line'),
              TextSpan(style: AppText.bodySmall.copyWith(color: Palette.inkDim), children: [
                TextSpan(text: '${r.overall}', style: AppText.readout.copyWith(fontSize: 13, color: Palette.instrumentInk)),
                const TextSpan(text: '/100'),
                // The style as the website shows it: the strategy's, else the profile's.
                if ((style ?? profile?.style) != null)
                  TextSpan(text: ' · ${style ?? profile!.style}', style: const TextStyle(fontWeight: FontWeight.w600, color: Palette.instrumentInk)),
                if (profile != null) TextSpan(text: ' · ${(profile!.lean.json ?? '').toLowerCase()} lean'),
                if (gapArea != null) TextSpan(text: ' · biggest gap ${gapArea.label.toLowerCase()}'),
              ]),
            )
          else
            Text('${team.members.length}/6 Pokémon', style: AppText.bodySmall.copyWith(color: Palette.mutedSlate)),
        ]),
      ),
    ]);
  }
}

class SlotTile extends ConsumerWidget {
  const SlotTile({super.key, required this.team, required this.slot, this.member, this.role});

  final TeamOut team;
  final int slot;
  final TeamMemberOut? member;
  final MemberRole? role;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final m = member;
    if (m == null) {
      return Card(
        key: Key('slot-$slot'),
        child: InkWell(
          borderRadius: BorderRadius.circular(Radii.card),
          onTap: () async {
            final pick = await pickPokemon(context);
            if (pick == null) return;
            try {
              // A form is saved as its species (dex number) + form id, as on the website.
              await ref.read(teamsRepositoryProvider).setSlot(
                team.id,
                slot,
                SlotUpdate(pokemonId: pick.formId != null ? pick.dexNumber : pick.id, formId: pick.formId),
              );
            } catch (e) {
              if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Couldn't add it: $e")));
            }
            invalidateTeamW(ref, team.id);
          },
          child: Center(
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              const Icon(Icons.add, color: Palette.mutedSlate),
              Text('Slot $slot', style: AppText.label.copyWith(color: Palette.mutedSlate)),
            ]),
          ),
        ),
      );
    }
    final base = ref.watch(serverAddressProvider);
    return Card(
      key: Key('slot-$slot'),
      child: InkWell(
        borderRadius: BorderRadius.circular(Radii.card),
        onTap: () => context.push('/teams/${team.id}/slot/$slot'),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(6, 6, 6, 8),
          child: Column(children: [
            Expanded(child: Center(child: Artwork(thumbUrl(base, m.spriteUrl), size: 72))),
            Text(m.name, maxLines: 1, overflow: TextOverflow.ellipsis, style: AppText.label.copyWith(fontSize: 13.5, color: Palette.instrumentInk)),
            Text(role?.role ?? '${m.moves.length}/4 moves', maxLines: 1, overflow: TextOverflow.ellipsis,
                style: AppText.label.copyWith(fontSize: 11.5, fontWeight: FontWeight.w500, color: Palette.mutedSlate)),
          ]),
        ),
      ),
    );
  }
}

class _OpponentPicker extends ConsumerWidget {
  const _OpponentPicker({required this.team, required this.opponentId});

  final TeamOut team;
  final int? opponentId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final others = (ref.watch(teamsListProvider).value ?? const <TeamSummary>[])
        .where((t) => t.id != team.id && t.size > 0)
        .toList();
    return Row(children: [
      Text('Compare with', style: AppText.label.copyWith(color: Palette.mutedSlate)),
      const SizedBox(width: Space.sm),
      Expanded(
        child: DropdownButton<int?>(
          key: const Key('opponent'),
          isExpanded: true,
          value: others.any((t) => t.id == opponentId) ? opponentId : null,
          hint: const Text('No opponent'),
          items: [
            const DropdownMenuItem<int?>(value: null, child: Text('No opponent')),
            for (final t in others) DropdownMenuItem<int?>(value: t.id, child: Text(t.name)),
          ],
          // The opponent lives in the URL (?vs=), as on the website.
          onChanged: (v) => context.replace(v == null ? '/teams/${team.id}' : '/teams/${team.id}?vs=$v'),
        ),
      ),
    ]);
  }
}
