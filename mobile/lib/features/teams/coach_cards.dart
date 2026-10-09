import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/export.dart';
import '../../data/server.dart';
import '../../data/sprites.dart';
import '../../theme/theme.dart';
import '../../theme/tokens.g.dart';
import '../../widgets/artwork.dart';
import '../../widgets/type_chip.dart';
import 'coach_state.dart';
import 'team_state.dart';

String _failure(Object e) => '$e'.replaceFirst('Exception: ', '');

/// A card's busy flag and error line, and one place to run a save from it.
mixin _Saving<T extends ConsumerStatefulWidget> on ConsumerState<T> {
  bool busy = false;
  String? error;

  /// Runs [save]; on success refreshes [teamId]'s page and returns true.
  Future<bool> run(int teamId, Future<Object?> Function() save) async {
    setState(() {
      busy = true;
      error = null;
    });
    try {
      await save();
      invalidateTeamW(ref, teamId);
      if (mounted) setState(() => busy = false);
      return true;
    } catch (e) {
      if (mounted) {
        setState(() {
          busy = false;
          error = _failure(e);
        });
      }
      return false;
    }
  }

  Widget errorLine() => error == null
      ? const SizedBox.shrink()
      : Padding(
          padding: const EdgeInsets.only(top: Space.xs),
          child: Text(error!, key: const Key('coach-card-error'), style: AppText.bodySmall.copyWith(color: Palette.pokeballRedText)),
        );
}

Widget _sprite(WidgetRef ref, String url, {double size = 36}) =>
    url.isEmpty ? SizedBox(width: size) : Artwork(thumbUrl(ref.watch(serverAddressProvider), url), size: size);

class _CoachCard extends StatelessWidget {
  const _CoachCard({required this.child, this.highlight = false});

  final Widget child;
  final bool highlight;

  @override
  Widget build(BuildContext context) => Container(
        margin: const EdgeInsets.only(top: Space.sm),
        padding: const EdgeInsets.all(Space.sm),
        decoration: BoxDecoration(
          color: Palette.panelWhite,
          borderRadius: BorderRadius.circular(Radii.inset),
          border: Border.all(color: highlight ? Palette.verdictGreen : Palette.hairline),
        ),
        child: child,
      );
}

// ---------------------------------------------------------------- set change

const _evShort = {'hp': 'HP', 'atk': 'Atk', 'def': 'Def', 'spa': 'SpA', 'spd': 'SpD', 'spe': 'Spe'};
String _evText(Map<String, int>? evs) {
  final parts = [for (final e in (evs ?? const {}).entries) if (e.value != 0) '${e.value} ${_evShort[e.key] ?? e.key}'];
  return parts.isEmpty ? 'none' : parts.join(' / ');
}

/// A proposed set, was → now. Nothing is saved until Apply; Revert puts the member back
/// exactly as it was; Dismiss hides the card.
class SetEditCard extends ConsumerStatefulWidget {
  const SetEditCard({super.key, required this.view});

  final SetEditView view;

  @override
  ConsumerState<SetEditCard> createState() => _SetEditCardState();
}

class _SetEditCardState extends ConsumerState<SetEditCard> with _Saving {
  bool applied = false;
  bool gone = false;

  @override
  Widget build(BuildContext context) {
    if (gone) return const SizedBox.shrink();
    final v = widget.view;
    final b = v.before;
    final a = v.after;
    final repo = ref.read(teamsRepositoryProvider);
    final rows = [
      ('Ability', b.ability ?? '—', a.ability ?? b.ability ?? '—'),
      ('Nature', b.nature ?? '—', a.nature ?? b.nature ?? '—'),
      ('Item', b.item ?? 'No item', a.item != null && a.item != 'None' ? a.item! : 'No item'),
      ('EVs', _evText(b.evs), _evText(a.evs)),
    ];
    final was = b.moves ?? const <String>[];
    final now = a.moves ?? const <String>[];
    return _CoachCard(
      highlight: applied,
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          _sprite(ref, v.spriteUrl),
          const SizedBox(width: Space.sm),
          Expanded(
            child: Text.rich(
              TextSpan(style: AppText.bodySmall, children: [
                TextSpan(text: applied ? 'Applied to ' : 'Proposed set for '),
                TextSpan(text: v.name, style: const TextStyle(fontWeight: FontWeight.w700)),
                if (v.side == SetEditViewSide.theirs) const TextSpan(text: ' (opponent)', style: TextStyle(fontStyle: FontStyle.italic)),
              ]),
            ),
          ),
        ]),
        const SizedBox(height: Space.xs),
        for (final (k, before, after) in rows)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 2),
            child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              SizedBox(width: 64, child: Text(k, style: AppText.bodySmall.copyWith(color: Palette.mutedSlate))),
              Expanded(
                child: before == after
                    ? Text(after, style: AppText.bodySmall)
                    : Text.rich(TextSpan(style: AppText.bodySmall, children: [
                        TextSpan(text: before, style: const TextStyle(decoration: TextDecoration.lineThrough, color: Palette.mutedSlate)),
                        const TextSpan(text: '  →  '),
                        TextSpan(text: after, style: const TextStyle(fontWeight: FontWeight.w700)),
                      ])),
              ),
            ]),
          ),
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 2),
          child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            SizedBox(width: 64, child: Text('Moves', style: AppText.bodySmall.copyWith(color: Palette.mutedSlate))),
            Expanded(
              child: Wrap(spacing: 6, runSpacing: 2, children: [
                for (final m in now)
                  Text(m, style: AppText.bodySmall.copyWith(fontWeight: was.contains(m) ? FontWeight.w400 : FontWeight.w700)),
                for (final m in was.where((m) => !now.contains(m)))
                  Text(m, style: AppText.bodySmall.copyWith(decoration: TextDecoration.lineThrough, color: Palette.mutedSlate)),
              ]),
            ),
          ]),
        ),
        const SizedBox(height: Space.xs),
        Wrap(spacing: Space.sm, children: [
          if (applied)
            OutlinedButton(
              key: const Key('set-revert'),
              onPressed: busy
                  ? null
                  : () async {
                      final ok = await run(v.teamId, () => repo.setSlot(v.teamId, v.slot, restoreUpdate(TeamMemberOut.fromJson(Map<String, dynamic>.from(v.member as Map)))));
                      if (ok && mounted) setState(() => applied = false);
                    },
              child: Text(busy ? '…' : 'Revert'),
            )
          else ...[
            FilledButton(
              key: const Key('set-apply'),
              onPressed: busy
                  ? null
                  : () async {
                      final ok = await run(v.teamId, () => repo.applyBuild(v.teamId, v.slot, SlotBuild.fromJson(Map<String, dynamic>.from(v.fields as Map))));
                      if (ok && mounted) setState(() => applied = true);
                    },
              child: Text(busy ? 'Saving…' : 'Apply'),
            ),
            TextButton(key: const Key('set-dismiss'), onPressed: () => setState(() => gone = true), child: const Text('Dismiss')),
          ],
        ]),
        errorLine(),
      ]),
    );
  }
}

// ---------------------------------------------------------------- candidates

/// Pokémon the coach suggests adding. Nothing changes until a button is pressed: Add fills
/// the first empty slot (Revert clears it); on a full team, Replace… picks a member to
/// swap out (Confirm, then Revert restores them).
class CandidateCards extends ConsumerWidget {
  const CandidateCards({super.key, required this.view});

  final CandidatesView view;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final team = ref.watch(teamProvider(view.teamId)).value;
    if (team == null) return const SizedBox.shrink();
    return Column(children: [for (final c in view.candidates) _CandidateCard(key: Key('cand-${c.pokemonId}'), c: c, team: team)]);
  }
}

class _CandidateCard extends ConsumerStatefulWidget {
  const _CandidateCard({super.key, required this.c, required this.team});

  final Candidate c;
  final TeamOut team;

  @override
  ConsumerState<_CandidateCard> createState() => _CandidateCardState();
}

class _CandidateCardState extends ConsumerState<_CandidateCard> with _Saving {
  int? addedTo; // slot the Add filled
  bool picking = false; // choosing who to replace
  int? replaceSlot; // picked, awaiting Confirm
  TeamMemberOut? replaced; // who was swapped out (for Revert)

  @override
  Widget build(BuildContext context) {
    final c = widget.c;
    final team = widget.team;
    final repo = ref.read(teamsRepositoryProvider);
    final full = team.members.length >= 6;
    Widget action;
    if (replaced != null) {
      action = _row([
        Text('Replaced ${replaced!.name}', style: AppText.bodySmall),
        OutlinedButton(
          key: const Key('cand-revert'),
          onPressed: busy
              ? null
              : () async {
                  final b = replaced!;
                  if (await run(team.id, () => repo.setSlot(team.id, b.slot, restoreUpdate(b))) && mounted) setState(() => replaced = null);
                },
          child: Text(busy ? '…' : 'Revert'),
        ),
      ]);
    } else if (addedTo != null) {
      action = _row([
        Text('Added to slot $addedTo', style: AppText.bodySmall),
        OutlinedButton(
          key: const Key('cand-revert'),
          onPressed: busy
              ? null
              : () async {
                  final s = addedTo!;
                  if (await run(team.id, () => repo.clearSlot(team.id, s)) && mounted) setState(() => addedTo = null);
                },
          child: Text(busy ? '…' : 'Revert'),
        ),
      ]);
    } else if (!full) {
      action = FilledButton(
        key: const Key('cand-add'),
        onPressed: busy
            ? null
            : () async {
                final s = firstEmptySlot(team);
                if (s == null) return;
                if (await run(team.id, () => repo.setSlot(team.id, s, SlotUpdate(pokemonId: c.pokemonId))) && mounted) setState(() => addedTo = s);
              },
        child: Text(busy ? 'Saving…' : 'Add'),
      );
    } else if (replaceSlot != null) {
      final out = team.members.firstWhere((m) => m.slot == replaceSlot);
      action = _row([
        Text('Replace ${out.name}?', style: AppText.bodySmall),
        FilledButton(
          key: const Key('cand-confirm'),
          onPressed: busy
              ? null
              : () async {
                  final before = out;
                  if (await run(team.id, () => repo.setSlot(team.id, before.slot, SlotUpdate(pokemonId: c.pokemonId))) && mounted) {
                    setState(() {
                      replaced = before;
                      replaceSlot = null;
                    });
                  }
                },
          child: Text(busy ? 'Saving…' : 'Confirm'),
        ),
        TextButton(onPressed: () => setState(() => replaceSlot = null), child: const Text('Cancel')),
      ]);
    } else if (picking) {
      final members = [...team.members]..sort((a, b) => a.slot.compareTo(b.slot));
      action = _row([
        Text('Replace who?', style: AppText.bodySmall),
        for (final m in members)
          InkWell(
            key: Key('cand-pick-${m.slot}'),
            onTap: () => setState(() {
              picking = false;
              replaceSlot = m.slot;
            }),
            child: Tooltip(message: m.name, child: _sprite(ref, m.spriteUrl, size: 32)),
          ),
        TextButton(onPressed: () => setState(() => picking = false), child: const Text('Cancel')),
      ]);
    } else {
      action = OutlinedButton(key: const Key('cand-replace'), onPressed: () => setState(() => picking = true), child: const Text('Replace…'));
    }
    return _CoachCard(
      highlight: addedTo != null || replaced != null,
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          _sprite(ref, c.spriteUrl, size: 40),
          const SizedBox(width: Space.sm),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(c.name, style: AppText.bodySmall.copyWith(fontWeight: FontWeight.w700)),
              Wrap(spacing: 4, runSpacing: 2, crossAxisAlignment: WrapCrossAlignment.center, children: [
                for (final t in c.types) TypeChip(t, dense: true),
                Text(c.role, style: AppText.bodySmall.copyWith(fontStyle: FontStyle.italic, color: Palette.inkDim)),
              ]),
              Text(c.reason, style: AppText.bodySmall.copyWith(color: Palette.inkDim)),
            ]),
          ),
        ]),
        const SizedBox(height: Space.xs),
        action,
        errorLine(),
      ]),
    );
  }

  Widget _row(List<Widget> children) =>
      Wrap(spacing: Space.sm, runSpacing: Space.xs, crossAxisAlignment: WrapCrossAlignment.center, children: children);
}

// ---------------------------------------------------------------- explicit add

/// "Added Garchomp to slot 4" with Undo (clears the slot), or why nothing was added.
class MemberAddedStrip extends ConsumerStatefulWidget {
  const MemberAddedStrip({super.key, required this.view});

  final MemberAddedView view;

  @override
  ConsumerState<MemberAddedStrip> createState() => _MemberAddedStripState();
}

class _MemberAddedStripState extends ConsumerState<MemberAddedStrip> with _Saving {
  bool undone = false;

  @override
  Widget build(BuildContext context) {
    final v = widget.view;
    final id = v.card.pokemonId;
    final text = undone
        ? 'Removed ${v.card.name} again.'
        : v.added
            ? 'Added ${v.card.name} to slot ${v.slot}'
            : v.message.replaceAll('**', '');
    return _CoachCard(
      highlight: v.added && !undone,
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          if (id != null) _sprite(ref, '/sprites/official-artwork/$id.png'),
          const SizedBox(width: Space.sm),
          Expanded(child: Text(text, key: const Key('added-text'), style: AppText.bodySmall)),
          if (v.added && !undone && v.slot != null)
            OutlinedButton(
              key: const Key('added-undo'),
              onPressed: busy
                  ? null
                  : () async {
                      if (await run(v.teamId, () => ref.read(teamsRepositoryProvider).clearSlot(v.teamId, v.slot!)) && mounted) {
                        setState(() => undone = true);
                      }
                    },
              child: Text(busy ? '…' : 'Undo'),
            ),
        ]),
        errorLine(),
      ]),
    );
  }
}

// ---------------------------------------------------------------- duel

const _outcome = {DuelOutOutcome.win: 'wins', DuelOutOutcome.lose: 'loses', DuelOutOutcome.even: 'is even'};

/// One pairing played out: who wins, who moves first, each side's moves, then the log.
class DuelCard extends StatelessWidget {
  const DuelCard({super.key, required this.view});

  final DuelView view;

  @override
  Widget build(BuildContext context) {
    final d = view.duel;
    String name(DuelEventSide s) => s == DuelEventSide.a ? d.ourName : d.theirName;
    final first = switch (d.first) {
      DuelOutFirst.ours => '${d.ourName} moves first',
      DuelOutFirst.theirs => '${d.theirName} moves first',
      _ => 'Speed tie',
    };
    final tone = switch (d.outcome) {
      DuelOutOutcome.win => Palette.verdictGreen,
      DuelOutOutcome.lose => Palette.pokeballRed,
      _ => Palette.hairline,
    };
    return Container(
      margin: const EdgeInsets.only(top: Space.sm),
      padding: const EdgeInsets.all(Space.sm),
      decoration: BoxDecoration(
        color: Palette.panelWhite,
        borderRadius: BorderRadius.circular(Radii.inset),
        border: Border.all(color: tone),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('${d.ourName} vs ${d.theirName}', style: AppText.title),
        Text('${d.ourName} ${_outcome[d.outcome] ?? ''} · $first', key: const Key('duel-outcome'), style: AppText.bodySmall.copyWith(color: Palette.inkDim)),
        const SizedBox(height: Space.xs),
        Text('${d.ourName}: ${d.ourMoves.isEmpty ? '—' : d.ourMoves.join(' · ')}', style: AppText.bodySmall),
        Text('${d.theirName}: ${d.theirMoves.isEmpty ? '—' : d.theirMoves.join(' · ')}', style: AppText.bodySmall),
        const SizedBox(height: Space.xs),
        for (final e in d.log.where((e) => e.kind != 'nothing').take(12))
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 1),
            child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              SizedBox(width: 30, child: Text('T${e.turn}', style: AppText.readout.copyWith(fontSize: 11, color: Palette.mutedSlate))),
              Expanded(
                child: Text.rich(TextSpan(style: AppText.bodySmall, children: [
                  TextSpan(text: name(e.side), style: const TextStyle(fontWeight: FontWeight.w700)),
                  TextSpan(
                    text: e.kind == 'attack' && e.move != null
                        ? ' uses ${e.move}${e.pct != null ? ' — ${e.pct!.round()}%' : ''}${e.mult != null && e.mult != 1 ? ' (${e.mult}×)' : ''}'
                        : e.kind == 'faint'
                            ? ' faints'
                            : ' ${_title(e.kind.replaceAll('-', ' '))}',
                  ),
                  if (e.hp != null && e.kind != 'faint')
                    TextSpan(text: ' · ${e.hp!.round()}% left', style: const TextStyle(color: Palette.mutedSlate)),
                ])),
              ),
            ]),
          ),
      ]),
    );
  }

  static String _title(String s) => s.split(' ').map((w) => w.isEmpty ? w : w[0].toUpperCase() + w.substring(1)).join(' ');
}
