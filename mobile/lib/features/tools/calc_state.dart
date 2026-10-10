import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/export.dart';
import '../../data/pokedex_repository.dart' show failureOf;
import '../../data/server.dart';
import '../teams/team_state.dart' show teamsRepositoryProvider;

const statKeys = ['hp', 'atk', 'def', 'spa', 'spd', 'spe'];
const statShort = {'hp': 'HP', 'atk': 'Atk', 'def': 'Def', 'spa': 'SpA', 'spd': 'SpD', 'spe': 'Spe'};
const maxEv = 252;
const maxEvTotal = 510;

Map<String, int> _evs([Map<String, int> p = const {}]) => {for (final k in statKeys) k: p[k] ?? 0};
Map<String, int> _ivs([Map<String, int> p = const {}]) => {for (final k in statKeys) k: p[k] ?? 31};

/// The Pokémon in a slot, with what the presets and move defaults need.
class CalcPick {
  const CalcPick({required this.pokemonId, this.formId, required this.name, required this.spriteUrl, required this.types,
      required this.attack, required this.spAttack});

  final int pokemonId; // the species (for a form, its base species)
  final int? formId;
  final String name;
  final String spriteUrl;
  final List<String> types;
  final int attack;
  final int spAttack;

  bool get physical => attack >= spAttack;

  // A provider key (its learnset): the same species or form is the same pick.
  @override
  bool operator ==(Object other) => other is CalcPick && other.pokemonId == pokemonId && other.formId == formId;
  @override
  int get hashCode => Object.hash(pokemonId, formId);
}

/// One slot's set. Presets are the website's: Offensive picks the spread matching the
/// Pokémon's category, Bulky is a physical wall, Custom once edited.
class CalcSet {
  const CalcSet({this.mon, this.pre = 'Offensive', this.nature = 'Adamant', required this.ev, required this.iv,
      this.item = 'None', this.ability = 'None', this.hp = 100, this.move});

  factory CalcSet.offensive([CalcPick? mon]) => (mon == null || mon.physical)
      ? CalcSet(mon: mon, nature: 'Adamant', ev: _evs({'atk': 252, 'spe': 252, 'hp': 4}), iv: _ivs())
      : CalcSet(mon: mon, nature: 'Modest', ev: _evs({'spa': 252, 'spe': 252, 'hp': 4}), iv: _ivs({'atk': 0}));
  factory CalcSet.bulky([CalcPick? mon]) =>
      CalcSet(mon: mon, pre: 'Bulky', nature: 'Bold', ev: _evs({'hp': 252, 'def': 252, 'spd': 4}), iv: _ivs());

  final CalcPick? mon;
  final String pre;
  final String nature;
  final Map<String, int> ev;
  final Map<String, int> iv;
  final String item;
  final String ability;
  final int hp; // current HP, % of max
  final String? move;

  int get evTotal => ev.values.fold(0, (a, b) => a + b);

  CalcSet copyWith({CalcPick? mon, String? pre, String? nature, Map<String, int>? ev, Map<String, int>? iv, String? item,
          String? ability, int? hp, String? move, bool clearMove = false}) =>
      CalcSet(
        mon: mon ?? this.mon,
        pre: pre ?? this.pre,
        nature: nature ?? this.nature,
        ev: ev ?? this.ev,
        iv: iv ?? this.iv,
        item: item ?? this.item,
        ability: ability ?? this.ability,
        hp: hp ?? this.hp,
        move: clearMove ? null : move ?? this.move,
      );

  /// One EV, capped at 252 and at what the 510 total leaves.
  CalcSet withEv(String k, int v) {
    final others = evTotal - (ev[k] ?? 0);
    return copyWith(pre: 'Custom', ev: {...ev, k: v.clamp(0, (maxEvTotal - others).clamp(0, maxEv))});
  }
}

class CalcModel {
  const CalcModel({
    this.level = 100,
    this.doubles = false,
    required this.sets,
    this.aims = const [2, 3, 0, 1],
    this.focus = 0,
    this.weather = 'None',
    this.terrain = 'None',
    this.reflect = false,
    this.lightscreen = false,
    this.crit = false,
    this.burn = false,
    this.friendGuard = false,
  });

  final int level;
  final bool doubles;
  final List<CalcSet> sets; // 0–1 yours (lead, partner), 2–3 theirs (left, right)
  final List<int> aims;
  final int focus;
  final String weather;
  final String terrain;
  final bool reflect;
  final bool lightscreen;
  final bool crit;
  final bool burn;
  final bool friendGuard;

  List<int> get active => doubles ? const [0, 1, 2, 3] : const [0, 2];

  CalcModel copyWith({int? level, bool? doubles, List<CalcSet>? sets, List<int>? aims, int? focus, String? weather, String? terrain,
          bool? reflect, bool? lightscreen, bool? crit, bool? burn, bool? friendGuard}) =>
      CalcModel(
        level: level ?? this.level,
        doubles: doubles ?? this.doubles,
        sets: sets ?? this.sets,
        aims: aims ?? this.aims,
        focus: focus ?? this.focus,
        weather: weather ?? this.weather,
        terrain: terrain ?? this.terrain,
        reflect: reflect ?? this.reflect,
        lightscreen: lightscreen ?? this.lightscreen,
        crit: crit ?? this.crit,
        burn: burn ?? this.burn,
        friendGuard: friendGuard ?? this.friendGuard,
      );

  /// What the server plays the turn from (active, filled slots only).
  CalcTurnRequest request() => CalcTurnRequest(
        level: level,
        doubles: doubles,
        field: CalcField(
          weather: weather, terrain: terrain, reflect: reflect, lightscreen: lightscreen, crit: crit, burn: burn,
          friendGuard: friendGuard,
        ),
        slots: [
          for (final i in active)
            if (sets[i].mon case final m?)
              CalcSlot(
                slot: i,
                pokemonId: m.pokemonId,
                formId: m.formId,
                name: m.name,
                nature: sets[i].nature,
                evs: sets[i].ev,
                ivs: sets[i].iv,
                item: sets[i].item,
                ability: sets[i].ability,
                hp: sets[i].hp,
                move: sets[i].move,
                aim: aims[i],
              ),
        ],
      );
}

/// A move as the calculator lists it: damaging moves first (STAB, then power), status after.
List<LearnsetMoveOut> calcMoveOrder(List<LearnsetMoveOut> moves, List<String> types) {
  final keep = moves.where((m) => m.type != null).toList();
  int b(bool x) => x ? 1 : 0;
  keep.sort((a, c) {
    final byDamage = b((a.power ?? 0) == 0) - b((c.power ?? 0) == 0);
    if (byDamage != 0) return byDamage;
    final byStab = b(types.contains(c.type)) - b(types.contains(a.type));
    if (byStab != 0) return byStab;
    final byPower = (c.power ?? 0) - (a.power ?? 0);
    return byPower != 0 ? byPower : a.name.compareTo(c.name);
  });
  return keep;
}

/// A Pokémon's learnset in calculator order.
final calcMovesProvider = FutureProvider.family<List<LearnsetMoveOut>, CalcPick>((ref, m) async {
  final all = await ref.watch(teamsRepositoryProvider).legalMoves(m.pokemonId, formId: m.formId);
  return calcMoveOrder(all, m.types);
});

/// What the damage maths models (items, abilities, weather, terrain, natures).
final calcOptionsProvider = FutureProvider<CalcOptionsOut>((ref) async {
  final dio = ref.watch(dioProvider);
  try {
    return await PokeragClient(dio).calcOptionsApiCalcOptionsGet();
  } on DioException catch (e) {
    throw failureOf(e, dio.options.baseUrl);
  }
});

/// The server's turn for a request (keyed by its JSON, so equal states share a fetch).
final calcTurnProvider = FutureProvider.autoDispose.family<CalcTurnOut, String>((ref, json) async {
  final dio = ref.watch(dioProvider);
  try {
    return await PokeragClient(dio).calcTurnRouteApiCalcTurnPost(
      body: CalcTurnRequest.fromJson(jsonDecode(json) as Map<String, dynamic>),
    );
  } on DioException catch (e) {
    throw failureOf(e, dio.options.baseUrl);
  }
});

final calcProvider = NotifierProvider<CalcNotifier, CalcModel>(CalcNotifier.new);

class CalcNotifier extends Notifier<CalcModel> {
  @override
  CalcModel build() {
    // The website opens on Garchomp (Offensive) against Corviknight (Bulky).
    Future.microtask(() async {
      await _loadDefault(0, '445');
      await _loadDefault(2, '823');
    });
    return CalcModel(sets: [CalcSet.offensive(), CalcSet.offensive(), CalcSet.bulky(), CalcSet.bulky()]);
  }

  Future<void> _loadDefault(int slot, String id) async {
    try {
      final d = await ref.read(repositoryProvider).detail(id);
      if (state.sets[slot].mon != null) return;
      await pick(slot, CalcPick(
        pokemonId: d.id, name: d.name, spriteUrl: d.spriteUrl, types: d.types,
        attack: d.stats.attack, spAttack: d.stats.spAttack,
      ));
    } catch (_) {
      // Offline: the slot stays empty and the turn shows the can't-reach state.
    }
  }

  void _set(int i, CalcSet s) => state = state.copyWith(sets: [for (final (k, x) in state.sets.indexed) k == i ? s : x]);
  void update(int i, CalcSet Function(CalcSet) f) => _set(i, f(state.sets[i]));

  /// A new Pokémon: on the Offensive preset it gets the spread for its category; its move
  /// and ability default as on the website (the first move of its category; an ability
  /// the maths models, else its first regular one).
  Future<void> pick(int i, CalcPick m) async {
    final cur = state.sets[i];
    final base = cur.pre == 'Offensive'
        ? CalcSet.offensive(m).copyWith(item: cur.item, hp: cur.hp)
        : cur.copyWith(mon: m, ability: 'None', clearMove: true);
    _set(i, base.copyWith(ability: 'None', clearMove: true));
    try {
      final moves = await ref.read(calcMovesProvider(m).future);
      final want = m.physical ? 'physical' : 'special';
      final first = moves.where((x) => x.damageClass == want).firstOrNull ?? moves.firstOrNull;
      if (state.sets[i].mon == m && first != null) update(i, (s) => s.copyWith(move: first.name));
    } catch (_) {}
    try {
      final abilities = await ref.read(teamsRepositoryProvider).abilities(m.pokemonId);
      final modelled = (await ref.read(calcOptionsProvider.future)).abilities.map((a) => a.name).toSet();
      final a = abilities.where((x) => modelled.contains(x.name)).firstOrNull ??
          abilities.where((x) => !x.isHidden).firstOrNull ??
          abilities.firstOrNull;
      if (state.sets[i].mon == m && a != null) update(i, (s) => s.copyWith(ability: a.name));
    } catch (_) {}
  }

  void preset(int i, String p) => update(i, (s) {
        final sp = p == 'Bulky' ? CalcSet.bulky(s.mon) : CalcSet.offensive(s.mon);
        return s.copyWith(pre: p, nature: sp.nature, ev: sp.ev, iv: sp.iv);
      });

  void clear(int i) => _set(i, i < 2 ? CalcSet.offensive() : CalcSet.bulky());
  void set(CalcModel Function(CalcModel) f) => state = f(state);
}
