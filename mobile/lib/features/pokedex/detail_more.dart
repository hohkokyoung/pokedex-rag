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
import '../../widgets/type_chip.dart';
import 'detail_sections.dart';
import 'detail_state.dart';

/// A section's own failure: a line and a Retry, so the rest of the page stays usable.
class SectionError extends StatelessWidget {
  const SectionError({super.key, required this.error, required this.onRetry});

  final Object error;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => Row(children: [
        Expanded(
          child: Text(
            error is Unreachable ? "Couldn't reach the server." : "The server couldn't load this.",
            style: AppText.bodySmall.copyWith(color: Palette.inkDim),
          ),
        ),
        TextButton(onPressed: onRetry, child: const Text('Retry')),
      ]);
}

Widget _kv(String k, Widget v) => Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        SizedBox(width: 128, child: Text(k, style: AppText.bodySmall.copyWith(color: Palette.mutedSlate))),
        Expanded(child: v),
      ]),
    );

Text _v(String s) => Text(s, style: AppText.bodySmall.copyWith(color: Palette.instrumentInk));

String _cap(String s) => s.isEmpty ? s : s[0].toUpperCase() + s.substring(1);

// ---------------------------------------------------------------- facts + training

/// Facts and training & breeding. Formatting mirrors the website's TrainingBreeding.
class FactsCard extends StatelessWidget {
  const FactsCard({super.key, required this.d, this.form});

  final PokemonDetail d;
  final FormOut? form;

  static const _evLabels = {
    'hp': 'HP',
    'attack': 'Attack',
    'defense': 'Defense',
    'sp_attack': 'Sp. Atk',
    'sp_defense': 'Sp. Def',
    'speed': 'Speed',
  };

  static String _pct(double n) => n == n.roundToDouble() ? n.toStringAsFixed(0) : n.toStringAsFixed(1);

  static String _thousands(int n) => n.toString().replaceAllMapped(RegExp(r'\B(?=(\d{3})+(?!\d))'), (_) => ',');

  @override
  Widget build(BuildContext context) {
    final height = form?.heightM ?? d.heightM;
    final weight = form?.weightKg ?? d.weightKg;
    final rate = d.genderRate;
    final ev = d.evYield;
    final evText = [for (final e in _evLabels.entries) if ((ev[e.key] ?? 0) > 0) '${ev[e.key]} ${e.value}'].join(', ');
    return Section(
      title: 'Facts & training',
      child: Column(children: [
        _kv('Height', _v(height == null ? '—' : '${height.toStringAsFixed(1)} m')),
        _kv('Weight', _v(weight == null ? '—' : '${weight.toStringAsFixed(1)} kg')),
        _kv('Habitat', _v(d.habitat == null ? '—' : _cap(d.habitat!))),
        _kv('Capture rate', _v('${d.captureRate ?? '—'}')),
        _kv('Base experience', _v('${d.baseExperience ?? '—'}')),
        _kv('Colour', _v(d.color == null ? '—' : _cap(d.color!))),
        _kv(
          'Gender ratio',
          rate == null || rate < 0
              ? Text('Genderless', style: AppText.bodySmall.copyWith(color: Palette.mutedSlate))
              : Text.rich(TextSpan(style: AppText.bodySmall, children: [
                  TextSpan(text: '♂ ${_pct(100 - rate / 8 * 100)}%', style: TextStyle(color: TypeColors.text['water'])),
                  const TextSpan(text: ' · ', style: TextStyle(color: Palette.faintSlate)),
                  TextSpan(text: '♀ ${_pct(rate / 8 * 100)}%', style: TextStyle(color: TypeColors.text['fairy'])),
                ])),
        ),
        _kv('Egg groups', _v(d.eggGroups.isEmpty ? '—' : d.eggGroups.join(', '))),
        _kv(
          'Egg cycles',
          _v(d.hatchCounter == null ? '—' : '${d.hatchCounter} cycles · ~${_thousands((d.hatchCounter! + 1) * 255)} steps'),
        ),
        _kv('Growth rate', _v(d.growthRate ?? '—')),
        _kv('EV yield', _v(evText.isEmpty ? 'None' : evText)),
        _kv('Base friendship', _v('${d.baseHappiness ?? '—'}')),
      ]),
    );
  }
}

// ---------------------------------------------------------------- moveset

/// The website's move groups; "Other" catches every remaining method.
const _groups = [
  ('Level-up', ['level-up']),
  ('Egg', ['egg']),
  ('TM / HM', ['machine']),
  ('Tutor', ['tutor']),
  ('Other', <String>[]),
];
const _known = {'level-up', 'egg', 'machine', 'tutor'};

bool _inGroup(String label, List<String> methods, String? m) =>
    label == 'Other' ? !_known.contains(m ?? '') : methods.contains(m ?? '');

class MovesetCard extends ConsumerStatefulWidget {
  const MovesetCard({super.key, required this.pokemonId});

  /// The species id, or a form's id (> 10000).
  final int pokemonId;

  @override
  ConsumerState<MovesetCard> createState() => _MovesetCardState();
}

class _MovesetCardState extends ConsumerState<MovesetCard> {
  int? _game; // null = the newest game, as the server picks
  String? _category; // physical | special | status
  String? _type;

  @override
  Widget build(BuildContext context) {
    final data = ref.watch(movesProvider((widget.pokemonId, _game)));
    return Section(
      title: 'Moveset',
      child: switch (data) {
        AsyncData(:final value) => _body(value),
        AsyncError(:final error) =>
          SectionError(error: error, onRetry: () => ref.invalidate(movesProvider((widget.pokemonId, _game)))),
        _ => const Padding(padding: EdgeInsets.all(Space.md), child: LinearProgressIndicator(minHeight: 2)),
      },
    );
  }

  Widget _body(PokemonGameMovesOut m) {
    if (m.games.isEmpty) return Text('No moves recorded for this Pokémon.', style: AppText.bodySmall);
    final game = m.versionGroupId ?? m.games.first.id;
    final types = {for (final mv in m.moves) if (mv.type != null) mv.type!}.toList()..sort();
    final rows = m.moves.where((mv) => (_category == null || mv.damageClass == _category) && (_type == null || mv.type == _type));
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      DropdownButton<int>(
        key: const Key('moveset-game'),
        value: game,
        isExpanded: true,
        style: AppText.body.copyWith(color: Palette.instrumentInk),
        items: [for (final g in m.games) DropdownMenuItem(value: g.id, child: Text('${g.name} · ${g.moves} moves'))],
        onChanged: (v) => setState(() => _game = v),
      ),
      const SizedBox(height: Space.xs),
      Wrap(spacing: 6, runSpacing: 6, children: [
        for (final (v, label) in const [(null, 'All'), ('physical', 'Physical'), ('special', 'Special'), ('status', 'Status')])
          ChoiceChip(
            key: Key('cat-${v ?? 'all'}'),
            label: Text(label),
            selected: _category == v,
            onSelected: (_) => setState(() => _category = v),
          ),
      ]),
      const SizedBox(height: Space.xs),
      DropdownButton<String?>(
        key: const Key('moveset-type'),
        value: _type,
        hint: const Text('Any type'),
        style: AppText.body.copyWith(color: Palette.instrumentInk),
        items: [
          const DropdownMenuItem<String?>(value: null, child: Text('Any type')),
          for (final t in types) DropdownMenuItem(value: t, child: Text(_cap(t))),
        ],
        onChanged: (v) => setState(() => _type = v),
      ),
      for (final (label, methods) in _groups)
        if (rows.any((mv) => _inGroup(label, methods, mv.learnMethod))) ...[
          const SizedBox(height: Space.sm),
          Text(
            '$label (${rows.where((mv) => _inGroup(label, methods, mv.learnMethod)).length})',
            style: AppText.label.copyWith(color: Palette.mutedSlate),
          ),
          for (final mv in rows.where((mv) => _inGroup(label, methods, mv.learnMethod)))
            _MoveRow(mv: mv, slot: label == 'Level-up' ? (mv.level == null || mv.level == 0 ? 'Evo' : '${mv.level}') : (mv.machine ?? '—'), game: game),
        ],
      if (rows.isEmpty) Padding(padding: const EdgeInsets.only(top: Space.sm), child: Text('No moves match.', style: AppText.bodySmall)),
    ]);
  }
}

class _MoveRow extends StatelessWidget {
  const _MoveRow({required this.mv, required this.slot, required this.game});

  final GameMoveOut mv;
  final String slot;
  final int game;

  @override
  Widget build(BuildContext context) => InkWell(
        key: Key('move-${mv.moveId}-${mv.learnMethod}'),
        onTap: () => showMoveSheet(context, mv, game),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 6),
          child: Row(children: [
            SizedBox(width: 52, child: Text(slot, style: AppText.readout.copyWith(color: Palette.mutedSlate))),
            Expanded(child: Text(mv.name, style: AppText.bodySmall.copyWith(fontWeight: FontWeight.w600))),
            if (mv.type != null) TypeChip(mv.type!, dense: true),
            SizedBox(
              width: 40,
              child: Text(mv.power?.toString() ?? '—', textAlign: TextAlign.right, style: AppText.readout),
            ),
          ]),
        ),
      );
}

/// A move's facts and who else learns it in the same game.
/// A move's details and who learns it in [game] (null: the newest game the server picks).
Future<void> showMoveSheet(BuildContext context, GameMoveOut mv, int? game) => showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      backgroundColor: Palette.panelWhite,
      builder: (_) => DraggableScrollableSheet(
        expand: false,
        initialChildSize: 0.75,
        maxChildSize: 0.95,
        builder: (context, scroll) => MoveSheet(mv: mv, game: game, scroll: scroll),
      ),
    );

/// Why no Pokémon learns a move (the website's lookup wording).
String unlearnableReason(GameMoveOut m) => m.name == 'Struggle'
    ? "No Pokémon learns Struggle; it's used automatically once every move is out of PP."
    : m.pp == 1
        ? 'Z-Move: no Pokémon learns it. A Z-Crystal turns a damaging move into it for one turn.'
        : RegExp(r'^(G-)?Max ').hasMatch(m.name)
            ? "Max Move: no Pokémon learns it. A Dynamaxed Pokémon's moves become it."
            : "No Pokémon learns this move in any game's regular learnset.";

class MoveSheet extends ConsumerWidget {
  const MoveSheet({super.key, required this.mv, required this.game, required this.scroll});

  final GameMoveOut mv;
  final int? game;
  final ScrollController scroll;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final learners = ref.watch(learnersProvider((mv.moveId, game)));
    final base = ref.watch(serverAddressProvider);
    String n(int? x) => x?.toString() ?? '—';
    return ListView(
      controller: scroll,
      padding: const EdgeInsets.fromLTRB(Space.gutter, 0, Space.gutter, Space.gutter * 2),
      children: [
        Text(mv.name, style: AppText.headline),
        const SizedBox(height: Space.xs),
        Wrap(spacing: 6, crossAxisAlignment: WrapCrossAlignment.center, children: [
          if (mv.type != null) TypeChip(mv.type!),
          if (mv.damageClass != null) Text(_cap(mv.damageClass!), style: AppText.label.copyWith(color: Palette.inkDim)),
        ]),
        const SizedBox(height: Space.sm),
        Text('Power ${n(mv.power)} · Accuracy ${n(mv.accuracy)} · PP ${n(mv.pp)}${mv.priority != 0 ? ' · Priority ${mv.priority > 0 ? '+' : ''}${mv.priority}' : ''}',
            style: AppText.readout),
        if (mv.shortEffect != null) ...[
          const SizedBox(height: Space.sm),
          Text(mv.shortEffect!, style: AppText.body),
        ],
        const SizedBox(height: Space.lg),
        switch (learners) {
          AsyncData(:final value) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(
                game == null
                    ? (value.learners.isEmpty ? unlearnableReason(mv) : '${value.learners.length} learn it in some game')
                    : '${value.learners.length} learn it in ${value.games.where((g) => g.id == game).firstOrNull?.name ?? 'this game'}',
                key: const Key('learners-line'),
                style: AppText.label.copyWith(color: Palette.mutedSlate),
              ),
              const SizedBox(height: Space.xs),
              for (final l in value.learners)
                ListTile(
                  key: Key('learner-${l.id}'),
                  contentPadding: EdgeInsets.zero,
                  dense: true,
                  leading: Artwork(thumbUrl(base, l.spriteUrl), size: 36),
                  title: Text(l.name, style: AppText.bodySmall.copyWith(fontWeight: FontWeight.w600)),
                  trailing: Wrap(spacing: 4, children: [for (final t in l.types) TypeChip(t, dense: true)]),
                  onTap: () {
                    Navigator.of(context).pop();
                    context.push(l.formId != null ? '/pokemon/${l.dexNumber}?form=${l.formId}' : '/pokemon/${l.dexNumber}');
                  },
                ),
            ]),
          AsyncError(:final error) =>
            SectionError(error: error, onRetry: () => ref.invalidate(learnersProvider((mv.moveId, game)))),
          _ => const LinearProgressIndicator(minHeight: 2),
        },
      ],
    );
  }
}

// ---------------------------------------------------------------- dex entries

class DexEntriesCard extends StatelessWidget {
  const DexEntriesCard({super.key, required this.entries});

  final List<FlavorEntry> entries;

  @override
  Widget build(BuildContext context) {
    final byGen = <String, List<FlavorEntry>>{};
    for (final e in entries) {
      byGen.putIfAbsent(e.generationLabel ?? 'Other', () => []).add(e);
    }
    return Section(
      title: 'Dex entries',
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        for (final MapEntry(key: gen, value: list) in byGen.entries) ...[
          Text(gen, style: AppText.label.copyWith(color: Palette.mutedSlate)),
          for (final e in list)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 5),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(e.text, style: AppText.bodySmall),
                Text((e.versions.isEmpty ? [e.version ?? ''] : e.versions).join(' · '),
                    style: AppText.readout.copyWith(fontSize: 10.5, color: Palette.mutedSlate)),
              ]),
            ),
          const SizedBox(height: Space.sm),
        ],
      ]),
    );
  }
}

// ---------------------------------------------------------------- where to find

class EncountersCard extends ConsumerStatefulWidget {
  const EncountersCard({super.key, required this.pokemonId});

  final int pokemonId;

  @override
  ConsumerState<EncountersCard> createState() => _EncountersCardState();
}

class _EncountersCardState extends ConsumerState<EncountersCard> {
  int? _version;

  @override
  Widget build(BuildContext context) {
    final data = ref.watch(encountersProvider((widget.pokemonId, _version)));
    return Section(
      title: 'Where to find',
      child: switch (data) {
        AsyncData(:final value) => _body(value),
        AsyncError(:final error) =>
          SectionError(error: error, onRetry: () => ref.invalidate(encountersProvider((widget.pokemonId, _version)))),
        _ => const Padding(padding: EdgeInsets.all(Space.md), child: LinearProgressIndicator(minHeight: 2)),
      },
    );
  }

  Widget _body(PokemonEncountersOut e) {
    if (e.games.isEmpty) {
      return Text('No wild encounters recorded. The data ends at Sword / Shield.', style: AppText.bodySmall);
    }
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      if (e.games.length > 1)
        DropdownButton<int>(
          key: const Key('encounters-game'),
          value: e.versionId ?? e.games.last.versionId,
          isExpanded: true,
          style: AppText.body.copyWith(color: Palette.instrumentInk),
          items: [for (final g in e.games) DropdownMenuItem(value: g.versionId, child: Text('${g.version} · ${g.places} places'))],
          onChanged: (v) => setState(() => _version = v),
        )
      else
        Text(e.games.single.version, style: AppText.label.copyWith(color: Palette.mutedSlate)),
      const SizedBox(height: Space.xs),
      for (final x in e.encounters)
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 5),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text([x.location, ?x.area].join(' · '), style: AppText.bodySmall.copyWith(fontWeight: FontWeight.w600)),
            Text(
              [
                x.methodName,
                x.minLevel == x.maxLevel ? 'Lv ${x.minLevel}' : 'Lv ${x.minLevel}–${x.maxLevel}',
                if (x.chance != null) '${x.chance}%',
                ?x.conditions,
              ].join(' · '),
              style: AppText.bodySmall.copyWith(color: Palette.inkDim),
            ),
          ]),
        ),
    ]);
  }
}
