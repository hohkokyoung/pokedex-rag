import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/export.dart';
import '../../data/errors.dart';
import '../../theme/theme.dart';
import '../../theme/tokens.g.dart';
import '../../widgets/ui.dart';
import '../../widgets/cant_reach.dart';
import '../pokedex/detail_sections.dart' show MatchupGroups, Section, matchGroups;
import '../pokedex/detail_state.dart' show typeChartProvider;
import '../pokedex/filters_sheet.dart' show TypeGrid;

/// What [attacker] does to a typing: the product over its types (the website's typingEff).
num typingEff(TypeChartOut c, String attacker, List<String> defs) =>
    defs.fold<num>(1, (f, d) => f * (c.chart[attacker]?[d] ?? 1));

/// The typing's defensive buckets and what its types hit ×2, read from the served chart
/// (the website's defensiveMatchups / superEffectiveHits), in the chart's order.
({List<String> x4, List<String> x2, List<String> half, List<String> quarter, List<String> immune, List<String> hits})
    typeCalc(TypeChartOut c, List<String> types) {
  List<String> at(num m) => [for (final a in c.order) if (typingEff(c, a, types) == m) a];
  return (
    x4: at(4),
    x2: at(2),
    half: at(0.5),
    quarter: at(0.25),
    immune: at(0),
    hits: [for (final d in c.order) if (types.any((t) => (c.chart[t]?[d] ?? 1) >= 2)) d],
  );
}

class TypeCalcScreen extends ConsumerStatefulWidget {
  const TypeCalcScreen({super.key});

  @override
  ConsumerState<TypeCalcScreen> createState() => _TypeCalcScreenState();
}

class _TypeCalcScreenState extends ConsumerState<TypeCalcScreen> {
  List<String> sel = ['fire'];

  @override
  Widget build(BuildContext context) {
    final chart = ref.watch(typeChartProvider);
    return Scaffold(
      appBar: pageBar('Type calculator'),
      body: switch (chart) {
        AsyncData(:final value) => ListView(
            padding: const EdgeInsets.fromLTRB(Space.gutter, 0, Space.gutter, Space.gutter * 2),
            children: [
              Card(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(Space.md, Space.md, Space.md, Space.md),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text('Defends as one or two types', style: AppText.bodySmall.copyWith(color: Palette.mutedSlate)),
                    const SizedBox(height: Space.sm),
                    // A third pick replaces the older of the two.
                    TypeGrid(keyPrefix: 'calc', types: value.order, selected: sel, max: 2, onChanged: (next) => setState(() => sel = next)),
                  ]),
                ),
              ),
              const SizedBox(height: Space.sm),
              if (sel.isNotEmpty) _result(typeCalc(value, sel)),
            ],
          ),
        AsyncError(:final error) when error is Unreachable =>
          CantReach(address: error.address, onRetry: () => ref.invalidate(typeChartProvider)),
        AsyncError() => Center(child: Text('The server had a problem loading the type chart.', style: AppText.body)),
        _ => const Center(child: Spinner()),
      },
    );
  }

  Widget _result(({List<String> x4, List<String> x2, List<String> half, List<String> quarter, List<String> immune, List<String> hits}) r) =>
      Section(
        title: sel.map((t) => t[0].toUpperCase() + t.substring(1)).join(' / '),
        child: MatchupGroups(
          groups: matchGroups(
            x4: r.x4,
            x2: r.x2,
            half: r.half,
            quarter: r.quarter,
            immune: r.immune,
            hits: r.hits,
            keyPrefix: 'calc-row',
          ),
        ),
      );
}
