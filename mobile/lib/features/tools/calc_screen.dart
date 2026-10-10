import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/export.dart';
import '../../data/errors.dart';
import '../../data/server.dart';
import '../../data/sprites.dart';
import '../../theme/theme.dart';
import '../../theme/tokens.g.dart';
import '../../widgets/ui.dart';
import '../../widgets/artwork.dart';
import '../../widgets/cant_reach.dart';
import '../../widgets/type_chip.dart';
import '../pokedex/detail_sections.dart' show Section;
import '../teams/pokemon_picker.dart' show pickPokemon;
import '../teams/team_state.dart' show abilitiesProvider;
import 'calc_coach_section.dart';
import 'calc_state.dart';

const _role = ['Lead', 'Partner', 'Left', 'Right'];
int _sideOf(int i) => i < 2 ? 0 : 1;
String _range(CalcHitOut h) => h.te == 0 ? 'immune' : '${h.minPct.toStringAsFixed(0)}–${h.maxPct.toStringAsFixed(0)}%';
Color _hpColor(num left) => left > 50 ? Palette.verdictGreen : left > 20 ? Palette.cautionAmber : Palette.pokeballRed;

/// Doubles targeting from the move's PokéAPI target (display only; the server plays it).
bool _aimable(String? target) => target == null || target == 'selected-pokemon' || target == 'random-opponent';

/// The website's damage calculator: set up both sides and the field; the server plays the turn.
class CalcScreen extends ConsumerStatefulWidget {
  const CalcScreen({super.key});

  @override
  ConsumerState<CalcScreen> createState() => _CalcScreenState();
}

class _CalcScreenState extends ConsumerState<CalcScreen> {
  CalcTurnOut? last; // shown while the next turn loads

  @override
  Widget build(BuildContext context) {
    final m = ref.watch(calcProvider);
    final req = jsonEncode(m.request().toJson());
    final turn = ref.watch(calcTurnProvider(req));
    if (turn case AsyncData(:final value)) last = value;
    final shown = turn.value ?? last;
    final focus = m.active.contains(m.focus) ? m.focus : (_sideOf(m.focus) == 0 ? 0 : 2);
    return Scaffold(
      appBar: pageBar('Damage calc'),
      body: switch (turn) {
        AsyncError(:final error) when error is Unreachable && shown == null =>
          CantReach(address: error.address, onRetry: () => ref.invalidate(calcTurnProvider(req))),
        _ => ListView(
            padding: const EdgeInsets.fromLTRB(Space.gutter, 0, Space.gutter, Space.gutter * 3),
            children: [
              _modeRow(m),
              const SizedBox(height: Space.sm),
              _roster(m, shown, focus),
              const SizedBox(height: Space.md),
              if (turn case AsyncError(:final error) when error is! Unreachable)
                Text('$error', key: const Key('calc-error'), style: AppText.bodySmall.copyWith(color: Palette.pokeballRedText)),
              _ThisTurn(model: m, turn: shown, loading: turn.isLoading),
              const SizedBox(height: Space.md),
              _SlotEditor(slot: focus, turn: shown),
              const SizedBox(height: Space.md),
              CalcCoachSection(focus: focus, turn: shown),
              const SizedBox(height: Space.md),
              _FieldCard(model: m),
              if (shown != null) _MathCard(turn: shown, focus: focus, model: m),
            ],
          ),
      },
    );
  }

  Widget _modeRow(CalcModel m) {
    final n = ref.read(calcProvider.notifier);
    return Row(children: [
      Expanded(
        child: Segmented<bool>(
          key: const Key('calc-mode'),
          compact: true,
          value: m.doubles,
          onChanged: (v) => n.set((s) => s.copyWith(doubles: v)),
          options: const [(false, 'Singles', null), (true, 'Doubles', null)],
        ),
      ),
      const SizedBox(width: 8),
      Expanded(
        child: Segmented<int>(
          key: const Key('calc-level'),
          compact: true,
          value: m.level,
          onChanged: (v) => n.set((s) => s.copyWith(level: v)),
          options: const [(50, 'Lv50', null), (100, 'Lv100', null)],
        ),
      ),
    ]);
  }

  Widget _roster(CalcModel m, CalcTurnOut? t, int focus) {
    final base = ref.watch(serverAddressProvider);
    Widget card(int i) {
      final s = m.sets[i];
      final out = t?.steps.expand((st) => st.hits).where((h) => h.attacker == i && !h.friendlyFire).toList() ?? const [];
      final best = out.isEmpty ? null : (out..sort((a, b) => b.maxPct.compareTo(a.maxPct))).first;
      final n = (t?.order.indexWhere((o) => o.slot == i) ?? -1) + 1;
      return Expanded(
        child: InkWell(
          key: Key('calc-slot-$i'),
          onTap: () async {
            if (s.mon == null) {
              await _pick(i);
            } else {
              ref.read(calcProvider.notifier).set((x) => x.copyWith(focus: i));
            }
          },
          child: Container(
            margin: const EdgeInsets.all(3),
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
            constraints: const BoxConstraints(minHeight: 62),
            decoration: BoxDecoration(
              // An empty slot is an outline on the ground; a filled one a white panel, the
              // focused one outlined in ink.
              color: s.mon == null ? Colors.transparent : Palette.panelWhite,
              borderRadius: BorderRadius.circular(Radii.card),
              border: Border.all(
                color: s.mon != null && i == focus ? Palette.instrumentInk : Palette.hairline,
                width: s.mon != null && i == focus ? 1.5 : 1,
              ),
            ),
            child: s.mon == null
                ? SizedBox(
                    height: 46,
                    child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                      const Icon(Icons.add, size: 16, color: Palette.mutedSlate),
                      const SizedBox(width: 4),
                      Flexible(
                        child: Text(
                          // Doubles slots are narrow: just the role there.
                          m.doubles ? _role[i] : (i >= 2 ? 'Add opponent' : 'Add ${_role[i].toLowerCase()}'),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: AppText.bodySmall.copyWith(color: Palette.mutedSlate),
                        ),
                      ),
                    ]),
                  )
                : Row(children: [
                    Artwork(thumbUrl(base, s.mon!.spriteUrl), size: 42),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text(s.mon!.name, maxLines: 1, overflow: TextOverflow.ellipsis, style: AppText.bodySmall.copyWith(fontWeight: FontWeight.w700)),
                        Text('${n > 0 ? '#$n · ' : ''}${s.move ?? 'No move yet'}',
                            maxLines: 1, overflow: TextOverflow.ellipsis, style: AppText.bodySmall.copyWith(fontSize: 12, color: Palette.mutedSlate)),
                        if (best != null) Text(_range(best), style: AppText.readout.copyWith(fontSize: 12)),
                        // HP left after the turn: solid = worst roll, faded = best roll.
                        if (t?.hp.where((x) => x.slot == i).firstOrNull case final hp?)
                          Padding(padding: const EdgeInsets.only(top: 4), child: _HpBar(lo: hp.lo, hi: hp.hi)),
                      ]),
                    ),
                  ]),
          ),
        ),
      );
    }

    Widget side(String label, List<int> slots) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Padding(padding: const EdgeInsets.only(left: 3), child: Text(label, style: AppText.label.copyWith(color: Palette.mutedSlate))),
          Row(children: [for (final i in slots) card(i)]),
        ]);
    // Singles: your Pokémon and the opponent side by side; doubles: a row per side.
    if (!m.doubles) {
      return Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Expanded(child: side('Your team', [0])),
        Expanded(child: side('Opponent', [2])),
      ]);
    }
    return Column(children: [side('Your team', [0, 1]), side('Opponent', [2, 3])]);
  }

  Future<void> _pick(int i) async {
    final p = await pickPokemon(context);
    if (p == null) return;
    var stats = p.stats;
    if (stats == null) {
      final d = await ref.read(repositoryProvider).detail('${p.dexNumber}');
      stats = d.stats;
    }
    await ref.read(calcProvider.notifier).pick(
          i,
          CalcPick(
            pokemonId: p.formId != null ? p.dexNumber : p.id, formId: p.formId, name: p.name, spriteUrl: p.spriteUrl,
            types: p.types, attack: stats.attack, spAttack: stats.spAttack,
          ),
        );
    ref.read(calcProvider.notifier).set((x) => x.copyWith(focus: i));
  }
}

/// The battle log in move order, as the server played it.
class _ThisTurn extends StatelessWidget {
  const _ThisTurn({required this.model, required this.turn, required this.loading});

  final CalcModel model;
  final CalcTurnOut? turn;
  final bool loading;

  @override
  Widget build(BuildContext context) {
    final t = turn;
    String? name(int i) => model.sets[i].mon?.name;
    InlineSpan who(int i, {bool cap = false}) => _sideOf(i) == 0
        ? TextSpan(text: name(i), style: const TextStyle(fontWeight: FontWeight.w700))
        : TextSpan(children: [
            TextSpan(text: '${cap ? 'The' : 'the'} opposing ', style: const TextStyle(color: Palette.mutedSlate)),
            TextSpan(text: name(i), style: const TextStyle(fontWeight: FontWeight.w700)),
          ]);
    final moveOf = {for (final mv in t?.moves ?? const <CalcMoveOut>[]) mv.slot: mv};
    final ordered = t?.order ?? const <CalcOrderOut>[];
    return Section(
      title: 'This turn',
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Expanded(child: Text('priority › speed', style: AppText.bodySmall.copyWith(color: Palette.mutedSlate))),
          if (loading) const Spinner(radius: 7),
        ]),
        if (t == null)
          const Padding(padding: EdgeInsets.all(Space.sm), child: LinearProgressIndicator(minHeight: 2))
        else if (ordered.isEmpty)
          Text('Pick a Pokémon on each side.', style: AppText.bodySmall)
        else
          for (final (idx, o) in ordered.indexed) _step(idx, o, t, moveOf, who, ordered),
      ]),
    );
  }

  Widget _step(int idx, CalcOrderOut o, CalcTurnOut t, Map<int, CalcMoveOut> moveOf, InlineSpan Function(int, {bool cap}) who,
      List<CalcOrderOut> ordered) {
    final st = t.steps.firstWhere((s) => s.slot == o.slot);
    final mv = moveOf[o.slot];
    final tie = ordered.any((x) => x.slot != o.slot && x.priority == o.priority && x.speed == o.speed);
    final lines = <Widget>[];
    Text line(List<InlineSpan> spans, {Key? key}) => Text.rich(TextSpan(style: AppText.bodySmall, children: spans), key: key);
    if (st.skipped) {
      lines.add(line([who(o.slot, cap: true), const TextSpan(text: ' fainted before it could move.')]));
    } else if (mv == null) {
      lines.add(line([const TextSpan(text: 'No move picked.', style: TextStyle(color: Palette.mutedSlate))]));
    } else {
      lines.add(line([who(o.slot, cap: true), TextSpan(text: ' used ${mv.name}!')]));
      if (mv.power <= 0) {
        lines.add(line([const TextSpan(text: 'Status move: no damage.', style: TextStyle(color: Palette.mutedSlate))]));
      } else if (st.hits.isEmpty) {
        lines.add(line([const TextSpan(text: 'But there was no target…', style: TextStyle(color: Palette.mutedSlate))]));
      }
      for (final h in st.hits) {
        if (h.te == 0) {
          lines.add(line([const TextSpan(text: "It doesn't affect "), who(h.target), const TextSpan(text: '…')]));
          continue;
        }
        final fx = h.te > 1 ? "It's super effective! " : h.te < 1 ? "It's not very effective… " : '';
        final hp = t.hp.firstWhere((x) => x.slot == h.target);
        lines.add(line([
          if (fx.isNotEmpty) TextSpan(text: fx, style: const TextStyle(color: Palette.mutedSlate)),
          who(h.target, cap: true),
          const TextSpan(text: ' lost '),
          TextSpan(text: _range(h), style: AppText.readout.copyWith(fontWeight: FontWeight.w700)),
          const TextSpan(text: ' of its HP'),
          if (h.friendlyFire) TextSpan(text: _sideOf(h.target) == 0 ? ' (your partner)' : ' (its partner)'),
          const TextSpan(text: '.'),
          if (h.sash) const TextSpan(text: ' It hung on using its Focus Sash!'),
          if (!h.sash && h.ko == CalcHitOutKo.maybe) const TextSpan(text: ' It could faint.'),
        ], key: Key('hit-${h.attacker}-${h.target}')));
        lines.add(_HpBar(lo: hp.lo, hi: hp.hi));
        if (h.ko == CalcHitOutKo.yes) {
          lines.add(line([who(h.target, cap: true), const TextSpan(text: ' fainted!', style: TextStyle(color: Palette.pokeballRedText, fontWeight: FontWeight.w700))]));
        }
      }
    }
    return Padding(
      key: Key('step-${o.slot}'),
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        SizedBox(width: 22, child: Text('${idx + 1}', style: AppText.readout.copyWith(color: Palette.mutedSlate))),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            ...lines,
            if (o.priority != 0 || tie || st.atRisk)
              Text(
                [
                  if (o.priority != 0) 'priority ${o.priority > 0 ? '+' : ''}${o.priority}',
                  if (tie) 'speed tie',
                  if (st.atRisk) "if it's still standing",
                ].join(' · '),
                style: AppText.readout.copyWith(fontSize: 10.5, color: Palette.mutedSlate),
              ),
          ]),
        ),
      ]),
    );
  }
}

/// HP left after the turn so far: solid = worst roll, faded = best roll.
class _HpBar extends StatelessWidget {
  const _HpBar({required this.lo, required this.hi});

  final num lo;
  final num hi;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 3),
        child: LayoutBuilder(
          builder: (_, c) => Container(
            height: 6,
            width: c.maxWidth,
            decoration: BoxDecoration(color: Palette.insetGray, borderRadius: BorderRadius.circular(3)),
            child: Stack(children: [
              Container(width: c.maxWidth * hi / 100, decoration: BoxDecoration(color: _hpColor(hi).withValues(alpha: 0.35), borderRadius: BorderRadius.circular(3))),
              Container(width: c.maxWidth * lo / 100, decoration: BoxDecoration(color: _hpColor(lo), borderRadius: BorderRadius.circular(3))),
            ]),
          ),
        ),
      );
}

/// The focused slot's set: Pokémon, move (and aim), ability, item, nature, preset, EVs, IVs, HP.
class _SlotEditor extends ConsumerWidget {
  const _SlotEditor({required this.slot, required this.turn});

  final int slot;
  final CalcTurnOut? turn;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final m = ref.watch(calcProvider);
    final s = m.sets[slot];
    final n = ref.read(calcProvider.notifier);
    final opts = ref.watch(calcOptionsProvider).value;
    if (s.mon == null) return const SizedBox.shrink();
    final mon = s.mon!;
    final moves = ref.watch(calcMovesProvider(mon)).value ?? const <LearnsetMoveOut>[];
    final abilities = ref.watch(abilitiesProvider(mon.pokemonId)).value ?? const <AbilityOut>[];
    final hint = {for (final a in opts?.abilities ?? const <CalcOptionOut>[]) a.name: a.note};
    final itemNote = {for (final i in opts?.items ?? const <CalcOptionOut>[]) i.name: i.note};
    final cur = moves.where((x) => x.name == s.move).firstOrNull;
    final foes = [for (final j in m.active) if (_sideOf(j) != _sideOf(slot) && m.sets[j].mon != null) j];
    final aim = turn?.aims['$slot'];
    // Settings rows: the label left, the choice right; a tap opens the check sheet.
    Widget drop(String key, String label, String value, List<(String, String?)> items, ValueChanged<String> on, {bool first = false}) =>
        PickerRow<String>(
          key: Key(key),
          label: label,
          value: value,
          placeholder: value,
          first: first,
          options: [for (final (v, note) in items) (v, v, note)],
          onChanged: on,
        );
    Future<void> change() async {
      final p = await pickPokemon(context);
      if (p == null) return;
      var stats = p.stats;
      stats ??= (await ref.read(repositoryProvider).detail('${p.dexNumber}')).stats;
      await n.pick(slot, CalcPick(
        pokemonId: p.formId != null ? p.dexNumber : p.id, formId: p.formId, name: p.name, spriteUrl: p.spriteUrl,
        types: p.types, attack: stats.attack, spAttack: stats.spAttack,
      ));
    }
    Widget stat(String label, String value, double v, double max, int divisions, ValueChanged<double> on, {Key? key}) => Row(children: [
          SizedBox(width: 44, child: Text(label, style: AppText.bodySmall.copyWith(color: Palette.inkDim))),
          Expanded(
            child: SliderTheme(
              data: SliderTheme.of(context).copyWith(padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 4)),
              child: Slider(key: key, value: v, min: 0, max: max, divisions: divisions, onChanged: on),
            ),
          ),
          SizedBox(width: 36, child: Text(value, textAlign: TextAlign.right, style: AppText.readout.copyWith(fontSize: 12))),
        ]);
    return Section(
      title: '${mon.name} · ${_role[slot]}',
      trailing: Row(mainAxisSize: MainAxisSize.min, children: [
        SquareButton(key: const Key('calc-change'), tooltip: 'Change Pokémon', icon: Icons.swap_horiz, size: 34, onPressed: change),
        if (slot == 1 || slot == 3) ...[
          const SizedBox(width: 6),
          SquareButton(key: const Key('calc-clear'), tooltip: 'Remove', icon: Icons.close, size: 34, onPressed: () => n.clear(slot)),
        ],
      ]),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Wrap(spacing: 6, children: [for (final t in mon.types) TypeChip(t, dense: true)]),
        const SizedBox(height: Space.sm),
        drop('calc-move', 'Move', s.move ?? '—', [
          for (final mv in moves) (mv.name, [?mv.type, ?mv.damageClass, '${mv.power ?? '—'}'].join(' · ')),
        ], (v) => n.update(slot, (x) => x.copyWith(move: v)), first: true),
        if (m.doubles && cur != null && (cur.power ?? 0) > 0 && _aimable(cur.target) && foes.length > 1)
          PickerRow<int>(
            key: const Key('calc-aim'),
            label: 'Target',
            value: aim ?? foes.first,
            keyOf: (label) => 'calc-aim-${foes.firstWhere((j) => m.sets[j].mon!.name == label, orElse: () => foes.first)}',
            options: [for (final j in foes) (j, m.sets[j].mon!.name, null)],
            onChanged: (j) => n.set((x) => x.copyWith(aims: [for (final (k, a) in x.aims.indexed) k == slot ? j : a])),
          ),
        drop('calc-ability', 'Ability', s.ability, [
          for (final a in abilities) (a.name, hint[a.name] ?? 'no damage effect'),
        ], (v) => n.update(slot, (x) => x.copyWith(ability: v))),
        drop('calc-item', 'Item', s.item, [
          ('None', 'no item'),
          for (final i in opts?.items ?? const <CalcOptionOut>[]) (i.name, itemNote[i.name]),
        ], (v) => n.update(slot, (x) => x.copyWith(item: v))),
        drop('calc-nature', 'Nature', s.nature, [for (final nat in opts?.natures ?? const <String>[]) (nat, null)],
            (v) => n.update(slot, (x) => x.copyWith(nature: v, pre: 'Custom'))),
        const SizedBox(height: Space.sm),
        Segmented<String>(
          key: const Key('calc-preset'),
          compact: true,
          value: s.pre,
          // Custom is what any edit makes; picking it changes nothing.
          onChanged: (v) => v == 'Custom' ? null : n.preset(slot, v),
          options: const [('Offensive', 'Offensive', null), ('Bulky', 'Bulky', null), ('Custom', 'Custom', null)],
        ),
        LabeledSlider(
          sliderKey: const Key('calc-hp'),
          label: 'HP left',
          value: '${s.hp}%',
          v: s.hp.toDouble(),
          min: 1,
          max: 100,
          onChanged: (v) => n.update(slot, (x) => x.copyWith(hp: v.round())),
        ),
        Padding(
          padding: const EdgeInsets.only(top: Space.xs, bottom: 2),
          child: Text('EVs ${s.evTotal} / $maxEvTotal', key: const Key('calc-ev-total'), style: AppText.bodySmall.copyWith(color: Palette.mutedSlate)),
        ),
        for (final k in statKeys)
          stat(statShort[k]!, '${s.ev[k] ?? 0}', (s.ev[k] ?? 0).toDouble(), maxEv.toDouble(), maxEv ~/ 4,
              (v) => n.update(slot, (x) => x.withEv(k, v.round())), key: Key('calc-ev-$k')),
        FoldRow(
          key: const Key('calc-ivs'),
          title: 'IVs ${statKeys.map((k) => s.iv[k]).join(' / ')}',
          child: Column(children: [
            for (final k in statKeys)
              stat(statShort[k]!, '${s.iv[k]}', (s.iv[k] ?? 31).toDouble(), 31, 31,
                  (v) => n.update(slot, (x) => x.copyWith(pre: 'Custom', iv: {...x.iv, k: v.round()}))),
          ]),
        ),
      ]),
    );
  }
}

/// Weather, terrain, screens, crit, burn, Friend Guard.
class _FieldCard extends ConsumerWidget {
  const _FieldCard({required this.model});

  final CalcModel model;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final m = model;
    final n = ref.read(calcProvider.notifier);
    final opts = ref.watch(calcOptionsProvider).value;
    Widget flag(String key, String label, bool on, CalcModel Function(bool) f) =>
        SwitchRow(key: Key('field-$key'), label: label, value: on, onChanged: (v) => n.set((_) => f(v)));
    final summary = [
      if (m.weather != 'None') m.weather,
      if (m.terrain != 'None') '${m.terrain} Terrain',
      if (m.reflect) 'Reflect',
      if (m.lightscreen) 'Light Screen',
      if (m.crit) 'crit',
      if (m.burn) 'burned',
      if (m.friendGuard) 'Friend Guard',
    ].join(' · ').ifEmpty('clear');
    return FoldPanel(
      key: const Key('calc-field'),
      title: 'Field',
      summary: summary,
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        PickerRow<String>(
          key: const Key('calc-weather'),
          label: 'Weather',
          first: true,
          value: m.weather,
          keyOf: (label) => 'weather-${label == 'None' ? 'None' : label}',
          options: [for (final w in opts?.weathers ?? const ['None']) (w, w, null)],
          onChanged: (w) => n.set((x) => x.copyWith(weather: w)),
        ),
        PickerRow<String>(
          key: const Key('calc-terrain'),
          label: 'Terrain',
          value: m.terrain,
          keyOf: (label) => 'terrain-$label',
          options: [for (final t in opts?.terrains ?? const ['None']) (t, t, null)],
          onChanged: (t) => n.set((x) => x.copyWith(terrain: t)),
        ),
        flag('reflect', 'Reflect', m.reflect, (v) => m.copyWith(reflect: v)),
        flag('lightscreen', 'Light Screen', m.lightscreen, (v) => m.copyWith(lightscreen: v)),
        flag('crit', 'Critical hit', m.crit, (v) => m.copyWith(crit: v)),
        flag('burn', 'Attacker burned', m.burn, (v) => m.copyWith(burn: v)),
        if (m.doubles) flag('friend-guard', 'Friend Guard', m.friendGuard, (v) => m.copyWith(friendGuard: v)),
      ]),
    );
  }
}

/// The focused Pokémon's hit (or the first hit), term by term, as the server computed it.
class _MathCard extends StatelessWidget {
  const _MathCard({required this.turn, required this.focus, required this.model});

  final CalcTurnOut turn;
  final int focus;
  final CalcModel model;

  @override
  Widget build(BuildContext context) {
    final all = turn.steps.expand((s) => s.hits).where((h) => h.te != 0);
    final h = all.where((h) => h.attacker == focus).firstOrNull ?? all.firstOrNull;
    if (h == null) return const SizedBox.shrink();
    String x(num n) => n % 1 == 0 ? '${n.toInt()}' : n.toStringAsFixed(3).replaceFirst(RegExp(r'0+$'), '');
    return FoldPanel(
      key: const Key('calc-math'),
      title: 'Math',
      summary: h.move,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(Space.sm),
        decoration: BoxDecoration(color: Palette.insetGray, borderRadius: BorderRadius.circular(Radii.inset)),
        child: Text(
          '${model.sets[h.attacker].mon?.name} → ${model.sets[h.target].mon?.name} (${h.move})\n'
          'Attack ${h.attack} vs Defence ${h.defense} · base damage ${h.baseValue}\n'
          '× ${x(h.mod)} modifiers × ${x(h.stab)} STAB × ${x(h.te)} type × 0.85–1 roll\n'
          '= ${_range(h)} of max HP${h.koHits > 0 ? ' · ${h.koHits}HKO from its current HP' : ''}',
          key: const Key('calc-math-text'),
          style: AppText.readout.copyWith(fontSize: 11, height: 1.6, fontWeight: FontWeight.w500, color: Palette.inkDim),
        ),
      ),
    );
  }
}

extension on String {
  String ifEmpty(String other) => isEmpty ? other : this;
}
