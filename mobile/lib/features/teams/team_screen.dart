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
import '../../widgets/type_chip.dart';
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
        title: Text(team.value?.name ?? '', style: AppText.headline),
        actions: [
          if (team.value != null)
            IconButton(
              key: const Key('rename'),
              tooltip: 'Rename',
              icon: const Icon(Icons.edit_outlined),
              onPressed: () async {
                final name = await askTeamName(context, team.value!.name);
                if (name == null || name.trim().isEmpty) return;
                await ref.read(teamsRepositoryProvider).rename(id, name.trim());
                invalidateTeamW(ref, id);
              },
            ),
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

class _Body extends ConsumerWidget {
  const _Body({required this.team, required this.opponentId});

  final TeamOut team;
  final int? opponentId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final rated = team.members.isEmpty ? null : ref.watch(teamAnalysisProvider((team.id, null))).value;
    return RefreshIndicator(
      onRefresh: () async => invalidateTeamW(ref, team.id),
      // Not lazy: the page is short, and the coach's thread and cards must stay built
      // (and laid out) while scrolled away.
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(Space.gutter, 0, Space.gutter, Space.gutter * 3),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          for (var slot = 1; slot <= 6; slot++)
            Padding(
              padding: const EdgeInsets.only(bottom: Space.xs),
              child: SlotTile(
                team: team,
                slot: slot,
                member: team.members.where((m) => m.slot == slot).firstOrNull,
                role: rated?.roles.members.where((r) => r.slot == slot).firstOrNull,
              ),
            ),
          const SizedBox(height: Space.md),
          if (team.members.isEmpty) ...[
            Text('Add your first Pokémon to rate the team.', style: AppText.body.copyWith(color: Palette.inkDim)),
            const SizedBox(height: Space.md),
            CoachSection(team: team),
          ] else ...[
            _OpponentPicker(team: team, opponentId: opponentId),
            if (opponentId != null) ...[
              const SizedBox(height: Space.md),
              MatchupCard(teamId: team.id, opponentId: opponentId!),
            ],
            const SizedBox(height: Space.md),
            CoachSection(team: team, opponentId: opponentId),
            const SizedBox(height: Space.md),
            TeamReport(team: team),
          ],
        ]),
      ),
    );
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
        child: ListTile(
          leading: const Icon(Icons.add_circle_outline),
          title: Text('Slot $slot · add a Pokémon', style: AppText.bodySmall.copyWith(color: Palette.inkDim)),
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
        ),
      );
    }
    final base = ref.watch(serverAddressProvider);
    final bst = m.baseStats.values.fold<int>(0, (a, b) => a + b);
    return Card(
      key: Key('slot-$slot'),
      child: InkWell(
        borderRadius: BorderRadius.circular(Radii.card),
        onTap: () => context.push('/teams/${team.id}/slot/$slot'),
        child: Padding(
          padding: const EdgeInsets.all(Space.sm),
          child: Row(children: [
            Artwork(thumbUrl(base, m.spriteUrl), size: 48),
            const SizedBox(width: Space.sm),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(m.name, style: AppText.title, overflow: TextOverflow.ellipsis),
                const SizedBox(height: 2),
                Wrap(spacing: 4, runSpacing: 4, children: [for (final t in m.types) TypeChip(t, dense: true)]),
                const SizedBox(height: 2),
                Text(
                  [
                    ?m.item?.name,
                    ?m.ability?.name,
                    '${m.moves.length}/4 moves',
                  ].join(' · '),
                  style: AppText.bodySmall.copyWith(color: Palette.inkDim),
                  overflow: TextOverflow.ellipsis,
                ),
              ]),
            ),
            Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
              Text('$bst', style: AppText.readout.copyWith(fontSize: 14)),
              Text(role?.role ?? 'BST', style: AppText.readout.copyWith(fontSize: 10, color: Palette.mutedSlate)),
            ]),
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
