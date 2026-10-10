import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/export.dart';
import '../../data/errors.dart';
import '../../theme/theme.dart';
import '../../theme/tokens.g.dart';
import '../../widgets/cant_reach.dart';
import '../teams/team_state.dart' show naturesProvider;

const _stats = ['attack', 'defense', 'sp_attack', 'sp_defense', 'speed'];
const _short = {'attack': 'Atk', 'defense': 'Def', 'sp_attack': 'SpA', 'sp_defense': 'SpD', 'speed': 'Spe'};

/// Neutral natures on the diagonal, by stat index (the website's grid).
const _diagonal = ['Hardy', 'Docile', 'Bashful', 'Quirky', 'Serious'];

class NatureScreen extends ConsumerStatefulWidget {
  const NatureScreen({super.key});

  @override
  ConsumerState<NatureScreen> createState() => _NatureScreenState();
}

class _NatureScreenState extends ConsumerState<NatureScreen> {
  String sel = 'Adamant';

  @override
  Widget build(BuildContext context) {
    final natures = ref.watch(naturesProvider);
    return Scaffold(
      appBar: AppBar(title: Text('Nature helper', style: AppText.headline)),
      body: switch (natures) {
        AsyncData(:final value) => _grid(value),
        AsyncError(:final error) when error is Unreachable =>
          CantReach(address: error.address, onRetry: () => ref.invalidate(naturesProvider)),
        AsyncError() => Center(child: Text('The server had a problem loading natures.', style: AppText.body)),
        _ => const Center(child: CircularProgressIndicator()),
      },
    );
  }

  Widget _grid(List<NatureOut> all) {
    final pair = {for (final n in all) if (n.increasedStat != null && n.decreasedStat != null) '${n.increasedStat}|${n.decreasedStat}': n.name};
    final cur = all.where((n) => n.name == sel).firstOrNull;
    Widget cell(String text, {bool head = false, bool diag = false, bool on = false, VoidCallback? tap, Color? color}) => Expanded(
          child: GestureDetector(
            onTap: tap,
            child: Container(
              key: tap == null ? null : Key('nature-$text'),
              height: 44,
              margin: const EdgeInsets.all(1.5),
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: on ? Palette.instrumentInk : (head ? null : (diag ? Palette.insetGray : Palette.panelWhite)),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Text(
                text,
                textAlign: TextAlign.center,
                style: (head ? AppText.readout.copyWith(fontSize: 11) : AppText.bodySmall.copyWith(fontSize: 11.5))
                    .copyWith(color: on ? Palette.panelWhite : color ?? (diag ? Palette.mutedSlate : Palette.instrumentInk)),
              ),
            ),
          ),
        );
    return ListView(
      padding: const EdgeInsets.fromLTRB(Space.gutter - 4, 0, Space.gutter - 4, Space.gutter * 2),
      children: [
        Row(children: [
          cell('+/−', head: true),
          for (final s in _stats) cell('−${_short[s]}', head: true, color: Palette.pokeballRedText),
        ]),
        for (final (r, up) in _stats.indexed)
          Row(children: [
            cell('+${_short[up]}', head: true, color: Palette.verdictGreenText),
            for (final (c, dn) in _stats.indexed)
              () {
                final name = r == c ? _diagonal[r] : pair['$up|$dn'] ?? '';
                return cell(name, diag: r == c, on: name == sel, tap: name.isEmpty ? null : () => setState(() => sel = name));
              }(),
          ]),
        const SizedBox(height: Space.md),
        Text.rich(
          key: const Key('nature-note'),
          TextSpan(style: AppText.body, children: [
            TextSpan(text: sel, style: const TextStyle(fontWeight: FontWeight.w700)),
            if (cur?.increasedStat != null) ...[
              const TextSpan(text: ' — '),
              TextSpan(text: '+${_short[cur!.increasedStat]}', style: const TextStyle(color: Palette.verdictGreenText)),
              const TextSpan(text: ' / '),
              TextSpan(text: '−${_short[cur.decreasedStat]}', style: const TextStyle(color: Palette.pokeballRedText)),
              const TextSpan(text: ' (±10%)'),
            ] else
              const TextSpan(text: ' — neutral, no stat changes'),
          ]),
        ),
      ],
    );
  }
}
