import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../api/export.dart';
import '../../data/server.dart';
import '../../data/sprites.dart';
import '../../theme/theme.dart';
import '../../theme/tokens.g.dart';
import '../../widgets/artwork.dart';
import '../../widgets/type_chip.dart';
import '../pokedex/detail_sections.dart' show Section;

/// A view's step-local refs → the answer's global [n] (sources carry step + step_index).
List<int> globalRefs(String? step, List<int>? refs, List<Source> sources) => [
      for (final r in refs ?? const <int>[])
        ?sources.where((s) => s.step == step && s.stepIndex == r).firstOrNull?.n,
    ];

const _statLabel = {
  'hp': 'HP',
  'attack': 'Attack',
  'defense': 'Defense',
  'sp_attack': 'Sp. Atk',
  'sp_defense': 'Sp. Def',
  'speed': 'Speed',
  'total': 'Total',
};

String _cap(String s) => s.isEmpty ? s : s[0].toUpperCase() + s.substring(1);

/// One card per Ask view; kinds this app doesn't draw (coach views) render nothing.
class ViewCard extends StatelessWidget {
  const ViewCard({super.key, required this.view, required this.sources, required this.onCite});

  final Object view; // a generated view class (see views.dart)
  final List<Source> sources;
  final void Function(int n) onCite;

  @override
  Widget build(BuildContext context) {
    final v = view;
    Widget card(String title, Widget body, String? step, List<int>? refs) => Section(
          title: title,
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            body,
            _Refs(refs: globalRefs(step, refs, sources), onCite: onCite),
          ]),
        );
    return switch (v) {
      RankingView() => card(
          '${v.order == RankingViewOrder.asc ? 'Lowest' : 'Highest'} ${_statLabel[v.stat] ?? v.stat} · ${v.total} match',
          Column(children: [
            for (final (i, r) in v.rows.indexed)
              _PokemonRow(
                name: r.name,
                dex: r.dexNumber,
                id: r.pokemonId,
                types: r.types ?? const [],
                lead: '${i + 1}',
                trailing: r.value == null ? null : (r.value! % 1 == 0 ? '${r.value!.toInt()}' : '${r.value}'),
                sub: r.via,
              ),
          ]),
          v.step,
          v.chunkRefs,
        ),
      PokemonListView() => card(
          v.title ?? 'Pokémon',
          Column(children: [
            for (final c in v.cards)
              _PokemonRow(name: c.name, dex: c.dexNumber, id: c.pokemonId, types: c.types ?? const [], sub: c.via ?? c.entry, trailing: c.total?.toString()),
          ]),
          v.step,
          v.chunkRefs,
        ),
      TypeChartView() => card(
          '${v.types.map(_cap).join('/')} matchups',
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            _types('Takes ×4', v.weak4x),
            _types('Takes ×2', v.weak2x),
            _types('Resists ×½', v.resistHalf),
            _types('Resists ×¼', v.resistQuarter),
            _types('Immune', v.immune),
            _types('Hits ×2', v.strongAgainst),
          ]),
          v.step,
          v.chunkRefs,
        ),
      MoveListView() => card(
          v.moves.length == 1 ? v.moves.single.name : 'Moves',
          Column(children: [for (final m in v.moves) _MoveBlock(m: m)]),
          v.step,
          v.chunkRefs,
        ),
      LearnsetView() => card(
          '${v.pokemon.name}${v.game != null ? ' · ${v.game}' : ''}',
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            for (final g in v.groups) ...[
              Padding(
                padding: const EdgeInsets.only(top: Space.sm, bottom: 2),
                child: Text('${_cap(g.label)} (${g.moves.length})', style: AppText.label.copyWith(color: Palette.mutedSlate)),
              ),
              for (final m in g.moves)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 3),
                  child: Row(children: [
                    SizedBox(width: 40, child: Text(m.level == null ? '' : (m.level == 0 ? 'Evo' : '${m.level}'), style: AppText.readout.copyWith(color: Palette.mutedSlate))),
                    Expanded(child: Text(m.name, style: AppText.bodySmall.copyWith(fontWeight: FontWeight.w600))),
                    TypeChip(m.type, dense: true),
                    SizedBox(width: 36, child: Text(m.power?.toString() ?? '—', textAlign: TextAlign.right, style: AppText.readout)),
                  ]),
                ),
            ],
          ]),
          v.step,
          v.chunkRefs,
        ),
      LearnersView() => card(
          '${v.total} learn ${v.move.name}${v.game != null ? ' in ${v.game}' : ''}',
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            if ((v.byMethod ?? const {}).isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(bottom: Space.xs),
                child: Text(
                  v.byMethod!.entries.map((e) => '${e.value} ${e.key == 'machine' ? 'by TM' : 'by ${e.key}'}').join(' · '),
                  style: AppText.bodySmall.copyWith(color: Palette.inkDim),
                ),
              ),
            if ((v.scope ?? const []).isNotEmpty)
              Text(v.scope!.join(' · '), style: AppText.bodySmall.copyWith(color: Palette.mutedSlate)),
            for (final c in v.rows)
              _PokemonRow(name: c.name, dex: c.dexNumber, id: c.pokemonId, types: c.types ?? const [], sub: c.via),
          ]),
          v.step,
          v.chunkRefs,
        ),
      LearnCheckView() => card(
          '${v.pokemon.name} × ${v.move.name}',
          Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Container(
              width: 36,
              height: 36,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: v.ok ? Palette.verdictGreen : Palette.pokeballRed,
                borderRadius: BorderRadius.circular(Radii.inset),
              ),
              child: Icon(v.ok ? Icons.check : Icons.close, color: Palette.panelWhite),
            ),
            const SizedBox(width: Space.sm),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(
                  v.absent
                      ? '${v.pokemon.name} isn\'t in ${v.game ?? 'that game'}.'
                      : (v.ok ? 'Yes${v.how != null ? ', ${v.how}' : ''}.' : 'No${v.how != null ? ': ${v.how}' : ''}.'),
                  key: const Key('learn-verdict'),
                  style: AppText.body.copyWith(fontWeight: FontWeight.w700),
                ),
                if (v.game != null) Text(v.game!, style: AppText.bodySmall.copyWith(color: Palette.mutedSlate)),
              ]),
            ),
          ]),
          v.step,
          v.chunkRefs,
        ),
      _ => const SizedBox.shrink(),
    };
  }

  Widget _types(String label, List<String>? types) => (types ?? const []).isEmpty
      ? const SizedBox.shrink()
      : Padding(
          padding: const EdgeInsets.symmetric(vertical: 4),
          child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            SizedBox(width: 88, child: Text(label, style: AppText.bodySmall.copyWith(color: Palette.mutedSlate))),
            Expanded(child: Wrap(spacing: 4, runSpacing: 4, children: [for (final t in types!) TypeChip(t, dense: true)])),
          ]),
        );
}

class _Refs extends StatelessWidget {
  const _Refs({required this.refs, required this.onCite});

  final List<int> refs;
  final void Function(int n) onCite;

  @override
  Widget build(BuildContext context) => refs.isEmpty
      ? const SizedBox.shrink()
      : Padding(
          padding: const EdgeInsets.only(top: Space.sm),
          child: Wrap(spacing: 2, crossAxisAlignment: WrapCrossAlignment.center, children: [
            Text('From ', style: AppText.bodySmall.copyWith(color: Palette.mutedSlate)),
            for (final n in refs.take(12))
              InkWell(
                onTap: () => onCite(n),
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 2, vertical: 4),
                  child: Text('[$n]', style: AppText.readout.copyWith(fontSize: 12, color: Palette.youBlueText)),
                ),
              ),
            if (refs.length > 12) Text('+${refs.length - 12}', style: AppText.bodySmall.copyWith(color: Palette.mutedSlate)),
          ]),
        );
}

class _PokemonRow extends ConsumerWidget {
  const _PokemonRow({required this.name, this.dex, this.id, this.types = const [], this.lead, this.trailing, this.sub});

  final String name;
  final int? dex;
  final int? id;
  final List<String> types;
  final String? lead;
  final String? trailing;
  final String? sub;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final base = ref.watch(serverAddressProvider);
    final sprite = id == null ? null : '/sprites/official-artwork/$id.png';
    return InkWell(
      onTap: dex == null ? null : () => context.push(id != null && id! > 10000 ? '/pokemon/$dex?form=$id' : '/pokemon/$dex'),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 5),
        child: Row(children: [
          if (lead != null) SizedBox(width: 22, child: Text(lead!, style: AppText.readout.copyWith(color: Palette.mutedSlate))),
          if (sprite != null) Artwork(thumbUrl(base, sprite), size: 36),
          const SizedBox(width: Space.sm),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(name, style: AppText.bodySmall.copyWith(fontWeight: FontWeight.w700)),
              if (types.isNotEmpty) Wrap(spacing: 4, children: [for (final t in types) TypeChip(t, dense: true)]),
              if (sub != null && sub!.isNotEmpty)
                Text(sub!, maxLines: 2, overflow: TextOverflow.ellipsis, style: AppText.bodySmall.copyWith(color: Palette.inkDim)),
            ]),
          ),
          if (trailing != null) Text(trailing!, style: AppText.readout.copyWith(fontSize: 14)),
        ]),
      ),
    );
  }
}

class _MoveBlock extends StatelessWidget {
  const _MoveBlock({required this.m});

  final MoveRow m;

  @override
  Widget build(BuildContext context) {
    String n(int? x) => x?.toString() ?? '—';
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Wrap(spacing: 8, runSpacing: 4, crossAxisAlignment: WrapCrossAlignment.center, children: [
          TypeChip(m.type, dense: true),
          if (m.damageClass != null) Text(_cap(m.damageClass!), style: AppText.bodySmall.copyWith(color: Palette.inkDim)),
          Text('Pow ${n(m.power)} · Acc ${n(m.accuracy)} · PP ${n(m.pp)}', style: AppText.readout.copyWith(fontSize: 11)),
        ]),
        if (m.effect != null) Padding(padding: const EdgeInsets.only(top: 4), child: Text(m.effect!, style: AppText.bodySmall)),
        if (m.learners != null)
          Text('${m.learners} Pokémon learn it', style: AppText.bodySmall.copyWith(color: Palette.mutedSlate)),
      ]),
    );
  }
}
