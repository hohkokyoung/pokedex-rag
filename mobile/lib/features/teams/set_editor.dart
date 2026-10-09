import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../api/export.dart';
import '../../data/errors.dart';
import '../../theme/theme.dart';
import '../../theme/tokens.g.dart';
import '../../widgets/type_chip.dart';
import '../pokedex/detail_state.dart';
import 'team_state.dart';

/// The server's limits (app/models/team.py); the editor never lets a set exceed them.
const maxEvPerStat = 252;
const maxEvTotal = 510;
const maxIv = 31;
const maxMoves = 4;

const statKeys = ['hp', 'attack', 'defense', 'sp_attack', 'sp_defense', 'speed'];
const statLabels = {'hp': 'HP', 'attack': 'Atk', 'defense': 'Def', 'sp_attack': 'SpA', 'sp_defense': 'SpD', 'speed': 'Spe'};

/// The editable state of one slot's set. Saving sends it whole (the server's PUT is a
/// full upsert).
class SetDraft {
  SetDraft.from(TeamMemberOut m)
      : pokemonId = m.pokemonId,
        formId = m.formId,
        abilityId = m.ability?.id,
        natureId = m.nature?.id,
        item = m.item == null ? null : (id: m.item!.id, name: m.item!.name),
        ev = {for (final k in statKeys) k: m.evSpread[k] ?? 0},
        iv = {for (final k in statKeys) k: m.ivSpread[k] ?? maxIv},
        moves = [for (final mv in m.moves) (id: mv.moveId, name: mv.name)];

  final int pokemonId;
  final int? formId;
  int? abilityId;
  int? natureId;
  ({int id, String name})? item;
  final Map<String, int> ev;
  final Map<String, int> iv;
  final List<({int id, String name})> moves;

  int get evTotal => ev.values.fold(0, (a, b) => a + b);

  /// Sets one EV, clamped to its own cap and to what the 510 total leaves.
  void setEv(String k, int v) {
    final others = evTotal - ev[k]!;
    ev[k] = v.clamp(0, (maxEvTotal - others).clamp(0, maxEvPerStat));
  }

  /// Adds a move unless the slot is full or already has it.
  bool addMove(int id, String name) {
    if (moves.length >= maxMoves || moves.any((m) => m.id == id)) return false;
    moves.add((id: id, name: name));
    return true;
  }

  SlotUpdate toUpdate() => SlotUpdate(
        pokemonId: pokemonId,
        formId: formId,
        abilityId: abilityId,
        natureId: natureId,
        itemId: item?.id,
        evSpread: evTotal > 0 ? Map.of(ev) : null,
        ivSpread: Map.of(iv),
        moveIds: moves.isEmpty ? null : [for (final m in moves) m.id],
      );
}

class SetEditor extends ConsumerWidget {
  const SetEditor({super.key, required this.teamId, required this.slot});

  final int teamId;
  final int slot;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final team = ref.watch(teamProvider(teamId));
    final member = team.value?.members.where((m) => m.slot == slot).firstOrNull;
    return switch (team) {
      AsyncData() when member != null => _Editor(teamId: teamId, member: member),
      AsyncData() => Scaffold(appBar: AppBar(), body: Center(child: Text('Slot $slot is empty.', style: AppText.body))),
      AsyncError(:final error) => Scaffold(appBar: AppBar(), body: Center(child: Text('$error', style: AppText.body))),
      _ => Scaffold(appBar: AppBar(), body: const Center(child: CircularProgressIndicator())),
    };
  }
}

class _Editor extends ConsumerStatefulWidget {
  const _Editor({required this.teamId, required this.member});

  final int teamId;
  final TeamMemberOut member;

  @override
  ConsumerState<_Editor> createState() => _EditorState();
}

class _EditorState extends ConsumerState<_Editor> {
  late final SetDraft d = SetDraft.from(widget.member);
  bool _saving = false;
  String? _error;

  Future<void> _save() async {
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      await ref.read(teamsRepositoryProvider).setSlot(widget.teamId, widget.member.slot, d.toUpdate());
      invalidateTeamW(ref, widget.teamId);
      if (mounted) context.pop();
    } on Rejected catch (e) {
      setState(() => _error = e.reason);
    } catch (e) {
      setState(() => _error = '$e');
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _remove() async {
    try {
      await ref.read(teamsRepositoryProvider).clearSlot(widget.teamId, widget.member.slot);
      invalidateTeamW(ref, widget.teamId);
      if (mounted) context.pop();
    } catch (e) {
      setState(() => _error = '$e');
    }
  }

  @override
  Widget build(BuildContext context) {
    final m = widget.member;
    return Scaffold(
      appBar: AppBar(
        title: Text(m.name, style: AppText.headline),
        actions: [
          TextButton(key: const Key('remove'), onPressed: _saving ? null : _remove, child: const Text('Remove')),
          Padding(
            padding: const EdgeInsets.only(right: Space.sm),
            child: FilledButton(key: const Key('save'), onPressed: _saving ? null : _save, child: Text(_saving ? 'Saving…' : 'Save')),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(Space.gutter, 0, Space.gutter, Space.gutter * 3),
        children: [
          Wrap(spacing: 4, children: [for (final t in m.types) TypeChip(t, dense: true)]),
          if (_error != null)
            Padding(
              padding: const EdgeInsets.only(top: Space.sm),
              child: Text(_error!, key: const Key('save-error'), style: AppText.bodySmall.copyWith(color: Palette.pokeballRedText)),
            ),
          _label('Ability'),
          _AbilityPicker(member: m, value: d.abilityId, onChanged: (v) => setState(() => d.abilityId = v)),
          _label('Nature'),
          _NaturePicker(value: d.natureId, onChanged: (v) => setState(() => d.natureId = v)),
          _label('Item'),
          _ItemPicker(value: d.item, onChanged: (v) => setState(() => d.item = v)),
          _label('Moves (${d.moves.length}/$maxMoves)'),
          Wrap(spacing: 6, runSpacing: 6, children: [
            for (final mv in d.moves)
              InputChip(
                key: Key('move-chip-${mv.id}'),
                label: Text(mv.name),
                onDeleted: () => setState(() => d.moves.remove(mv)),
              ),
            ActionChip(
              key: const Key('add-move'),
              avatar: const Icon(Icons.add, size: 16),
              label: const Text('Add move'),
              onPressed: d.moves.length >= maxMoves
                  ? null
                  : () async {
                      final pick = await _pickMove(context, m);
                      if (pick != null) setState(() => d.addMove(pick.moveId, pick.name));
                    },
            ),
          ]),
          _label('EVs (${d.evTotal}/$maxEvTotal)'),
          for (final k in statKeys)
            _StatSlider(
              key: Key('ev-$k'),
              label: statLabels[k]!,
              value: d.ev[k]!,
              max: maxEvPerStat,
              divisions: maxEvPerStat ~/ 4,
              onChanged: (v) => setState(() => d.setEv(k, v)),
            ),
          _label('IVs'),
          for (final k in statKeys)
            _StatSlider(
              key: Key('iv-$k'),
              label: statLabels[k]!,
              value: d.iv[k]!,
              max: maxIv,
              divisions: maxIv,
              onChanged: (v) => setState(() => d.iv[k] = v.clamp(0, maxIv)),
            ),
        ],
      ),
    );
  }

  Widget _label(String s) => Padding(
        padding: const EdgeInsets.only(top: Space.lg, bottom: Space.xs),
        child: Text(s, style: AppText.label.copyWith(color: Palette.mutedSlate)),
      );

  Future<LearnsetMoveOut?> _pickMove(BuildContext context, TeamMemberOut m) => showModalBottomSheet<LearnsetMoveOut>(
        context: context,
        isScrollControlled: true,
        showDragHandle: true,
        backgroundColor: Palette.panelWhite,
        builder: (_) => FractionallySizedBox(
          heightFactor: 0.85,
          child: _MovePicker(pokemonId: m.pokemonId, formId: m.formId, taken: {for (final x in d.moves) x.id}),
        ),
      );
}

class _StatSlider extends StatelessWidget {
  const _StatSlider({super.key, required this.label, required this.value, required this.max, required this.divisions, required this.onChanged});

  final String label;
  final int value;
  final int max;
  final int divisions;
  final ValueChanged<int> onChanged;

  @override
  Widget build(BuildContext context) => Row(children: [
        SizedBox(width: 40, child: Text(label, style: AppText.bodySmall)),
        Expanded(
          child: Slider(
            value: value.toDouble(),
            max: max.toDouble(),
            divisions: divisions,
            onChanged: (v) => onChanged(v.round()),
          ),
        ),
        SizedBox(width: 36, child: Text('$value', textAlign: TextAlign.right, style: AppText.readout)),
      ]);
}

class _AbilityPicker extends ConsumerWidget {
  const _AbilityPicker({required this.member, required this.value, required this.onChanged});

  final TeamMemberOut member;
  final int? value;
  final ValueChanged<int?> onChanged;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // A form has its own abilities (from the detail response); a species uses the builder list.
    final List<({int id, String name, bool hidden})> options;
    if (member.formId != null) {
      final detail = ref.watch(detailProvider('${member.dexNumber}')).value;
      final form = detail?.forms.where((f) => f.id == member.formId).firstOrNull;
      options = [for (final a in form?.abilities ?? const <FormAbilityOut>[]) if (a.id != null) (id: a.id!, name: a.name, hidden: a.isHidden)];
    } else {
      final list = ref.watch(abilitiesProvider(member.pokemonId)).value ?? const <AbilityOut>[];
      options = [for (final a in list) (id: a.id, name: a.name, hidden: a.isHidden)];
    }
    return DropdownButton<int?>(
      key: const Key('ability'),
      isExpanded: true,
      value: options.any((o) => o.id == value) ? value : null,
      hint: const Text('No ability'),
      items: [
        const DropdownMenuItem<int?>(value: null, child: Text('No ability')),
        for (final o in options) DropdownMenuItem<int?>(value: o.id, child: Text(o.hidden ? '${o.name} (hidden)' : o.name)),
      ],
      onChanged: onChanged,
    );
  }
}

class _NaturePicker extends ConsumerWidget {
  const _NaturePicker({required this.value, required this.onChanged});

  final int? value;
  final ValueChanged<int?> onChanged;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final natures = ref.watch(naturesProvider).value ?? const <NatureOut>[];
    String label(NatureOut n) => n.increasedStat == null
        ? '${n.name} (neutral)'
        : '${n.name} (+${statLabels[n.increasedStat] ?? n.increasedStat} −${statLabels[n.decreasedStat] ?? n.decreasedStat})';
    return DropdownButton<int?>(
      key: const Key('nature'),
      isExpanded: true,
      value: natures.any((n) => n.id == value) ? value : null,
      hint: const Text('No nature'),
      items: [
        const DropdownMenuItem<int?>(value: null, child: Text('No nature')),
        for (final n in natures) DropdownMenuItem<int?>(value: n.id, child: Text(label(n))),
      ],
      onChanged: onChanged,
    );
  }
}

class _ItemPicker extends ConsumerStatefulWidget {
  const _ItemPicker({required this.value, required this.onChanged});

  final ({int id, String name})? value;
  final ValueChanged<({int id, String name})?> onChanged;

  @override
  ConsumerState<_ItemPicker> createState() => _ItemPickerState();
}

class _ItemPickerState extends ConsumerState<_ItemPicker> {
  final _field = TextEditingController();
  Timer? _debounce;
  List<ItemOut> _results = const [];

  @override
  void dispose() {
    _debounce?.cancel();
    _field.dispose();
    super.dispose();
  }

  void _search(String q) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 250), () async {
      final r = q.trim().isEmpty ? const <ItemOut>[] : await ref.read(teamsRepositoryProvider).heldItems(q.trim());
      if (mounted) setState(() => _results = r);
    });
  }

  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Expanded(child: Text(widget.value?.name ?? 'No item', key: const Key('item-current'), style: AppText.body)),
          if (widget.value != null) TextButton(onPressed: () => widget.onChanged(null), child: const Text('Clear')),
        ]),
        TextField(
          key: const Key('item-search'),
          controller: _field,
          autocorrect: false,
          onChanged: _search,
          decoration: const InputDecoration(prefixIcon: Icon(Icons.search), hintText: 'Search held items', isDense: true),
        ),
        for (final it in _results.take(6))
          ListTile(
            key: Key('item-${it.id}'),
            dense: true,
            contentPadding: EdgeInsets.zero,
            title: Text(it.name, style: AppText.bodySmall.copyWith(fontWeight: FontWeight.w600)),
            subtitle: it.shortEffect == null ? null : Text(it.shortEffect!, maxLines: 2, overflow: TextOverflow.ellipsis, style: AppText.bodySmall),
            onTap: () {
              widget.onChanged((id: it.id, name: it.name));
              _field.clear();
              setState(() => _results = const []);
            },
          ),
      ]);
}

/// The species' (or form's) learnset, searchable; moves already on the set are hidden.
class _MovePicker extends ConsumerStatefulWidget {
  const _MovePicker({required this.pokemonId, required this.formId, required this.taken});

  final int pokemonId;
  final int? formId;
  final Set<int> taken;

  @override
  ConsumerState<_MovePicker> createState() => _MovePickerState();
}

class _MovePickerState extends ConsumerState<_MovePicker> {
  String _q = '';

  @override
  Widget build(BuildContext context) {
    final moves = ref.watch(legalMovesProvider((widget.pokemonId, widget.formId)));
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: Space.gutter),
      child: Column(children: [
        TextField(
          key: const Key('move-search'),
          autofocus: true,
          autocorrect: false,
          onChanged: (v) => setState(() => _q = v.trim().toLowerCase()),
          decoration: const InputDecoration(prefixIcon: Icon(Icons.search), hintText: 'Search its moves', isDense: true),
        ),
        const SizedBox(height: Space.sm),
        Expanded(
          child: switch (moves) {
            AsyncData(:final value) => ListView(children: [
                for (final mv in value)
                  if (!widget.taken.contains(mv.moveId) && (_q.isEmpty || mv.name.toLowerCase().contains(_q)))
                    ListTile(
                      key: Key('pick-move-${mv.moveId}'),
                      contentPadding: EdgeInsets.zero,
                      dense: true,
                      title: Text(mv.name, style: AppText.bodySmall.copyWith(fontWeight: FontWeight.w600)),
                      subtitle: mv.shortEffect == null ? null : Text(mv.shortEffect!, maxLines: 1, overflow: TextOverflow.ellipsis),
                      trailing: Row(mainAxisSize: MainAxisSize.min, children: [
                        if (mv.type != null) TypeChip(mv.type!, dense: true),
                        SizedBox(width: 36, child: Text(mv.power?.toString() ?? '—', textAlign: TextAlign.right, style: AppText.readout)),
                      ]),
                      onTap: () => Navigator.pop(context, mv),
                    ),
              ]),
            AsyncError(:final error) => Center(child: Text("Couldn't load its moves: $error", style: AppText.bodySmall)),
            _ => const Center(child: CircularProgressIndicator()),
          },
        ),
      ]),
    );
  }
}
