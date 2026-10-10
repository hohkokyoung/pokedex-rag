import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/export.dart';
import '../../data/errors.dart';
import '../../data/pokedex_repository.dart' show failureOf;
import '../../data/server.dart';
import '../../data/sprites.dart';
import '../../theme/theme.dart';
import '../../theme/tokens.g.dart';
import '../../widgets/ui.dart';
import '../../widgets/artwork.dart';
import '../../widgets/cant_reach.dart';
import '../teams/pokemon_picker.dart' show pickPokemon;

/// The situation the server ranks balls for (a record, so equal situations share a fetch).
typedef CatchQuery = ({
  int pokemonId,
  int level,
  int myLevel,
  int hpPct,
  int turn,
  Status status,
  bool night,
  bool water,
  bool caught,
  bool loveMatch,
  int dexCaught,
  bool charm,
});

/// The server's ranking for a situation; the app never computes catch odds itself.
final catchProvider = FutureProvider.autoDispose.family<CatchOut, CatchQuery>((ref, q) async {
  final dio = ref.watch(dioProvider);
  try {
    return await PokeragClient(dio).catchOddsApiPokemonPokemonIdCatchGet(
      pokemonId: q.pokemonId,
      level: q.level,
      myLevel: q.myLevel,
      hpPct: q.hpPct,
      turn: q.turn,
      status: q.status,
      night: q.night,
      water: q.water,
      caught: q.caught,
      loveMatch: q.loveMatch,
      dexCaught: q.dexCaught,
      charm: q.charm,
    );
  } on DioException catch (e) {
    throw failureOf(e, dio.options.baseUrl);
  }
});

const _statuses = [
  (Status.sleep, 'SLP', 'Asleep'),
  (Status.freeze, 'FRZ', 'Frozen'),
  (Status.paralysis, 'PAR', 'Paralyzed'),
  (Status.burn, 'BRN', 'Burned'),
  (Status.poison, 'PSN', 'Poisoned'),
];

String pctText(num p) => p >= 1
    ? '100'
    : p >= 0.995
    ? '>99'
    : p < 0.001
    ? '<0.1'
    : (p * 100).toStringAsFixed(p < 0.1 ? 1 : 0);

class CatchScreen extends ConsumerStatefulWidget {
  const CatchScreen({super.key});

  @override
  ConsumerState<CatchScreen> createState() => _CatchScreenState();
}

class _CatchScreenState extends ConsumerState<CatchScreen> {
  // The website tile's opening situation: Dragonite, Lv 55, a quarter of its HP.
  String name = 'Dragonite';
  CatchQuery q = (
    pokemonId: 149,
    level: 55,
    myLevel: 30,
    hpPct: 25,
    turn: 1,
    status: Status.none,
    night: false,
    water: false,
    caught: false,
    loveMatch: false,
    dexCaught: 0,
    charm: false,
  );
  int? hpDrag; // the HP slider while dragging (asks the server on release)
  String ball = 'ultra';
  CatchOut? last; // shown while the next ranking loads

  CatchQuery _with({
    int? pokemonId,
    int? level,
    int? myLevel,
    int? hpPct,
    int? turn,
    Status? status,
    bool? night,
    bool? water,
    bool? caught,
    bool? loveMatch,
    int? dexCaught,
    bool? charm,
  }) => (
    pokemonId: pokemonId ?? q.pokemonId,
    level: level ?? q.level,
    myLevel: myLevel ?? q.myLevel,
    hpPct: hpPct ?? q.hpPct,
    turn: turn ?? q.turn,
    status: status ?? q.status,
    night: night ?? q.night,
    water: water ?? q.water,
    caught: caught ?? q.caught,
    loveMatch: loveMatch ?? q.loveMatch,
    dexCaught: dexCaught ?? q.dexCaught,
    charm: charm ?? q.charm,
  );

  void _set(CatchQuery next) => setState(() => q = next);

  @override
  Widget build(BuildContext context) {
    final odds = ref.watch(catchProvider(q));
    if (odds case AsyncData(:final value)) last = value;
    final shown = odds.value ?? last;
    final base = ref.watch(serverAddressProvider);
    if (odds case AsyncError(:final error) when error is Unreachable && shown == null) {
      return Scaffold(
        appBar: pageBar('Catch rate'),
        body: CantReach(address: error.address, onRetry: () => ref.invalidate(catchProvider(q))),
      );
    }
    final top = shown?.balls.where((b) => b.id == ball).firstOrNull ?? shown?.balls.firstOrNull;
    return Scaffold(
      appBar: pageBar('Catch rate'),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(Space.gutter, 0, Space.gutter, Space.gutter * 3),
        children: [
          Card(
            child: ListTile(
              key: const Key('catch-pick'),
              leading: Artwork(thumbUrl(base, '/sprites/official-artwork/${q.pokemonId}.png'), size: 44),
              title: Text(name, style: AppText.title),
              subtitle: Text('Base catch rate ${shown?.captureRate ?? '–'}', style: AppText.readout.copyWith(color: Palette.inkDim)),
              trailing: const Icon(Icons.swap_horiz),
              onTap: () async {
                final p = await pickPokemon(context);
                if (p == null) return;
                setState(() {
                  name = p.name;
                  q = _with(pokemonId: p.dexNumber);
                });
              },
            ),
          ),
          const SizedBox(height: Space.sm),
          Text('Status', style: AppText.label.copyWith(color: Palette.mutedSlate)),
          const SizedBox(height: 4),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: [
              for (final (s, code, label) in _statuses)
                ChoiceChip(
                  key: Key('status-${s.json}'),
                  label: Text(code),
                  tooltip: label,
                  selected: q.status == s,
                  onSelected: (_) => _set(_with(status: q.status == s ? Status.none : s)),
                ),
            ],
          ),
          _slider(
            'HP left',
            '${hpDrag ?? q.hpPct}%${top != null && hpDrag == null ? ' · ${top.terms.hp}/${top.terms.maxHp}' : ''}',
            (hpDrag ?? q.hpPct).toDouble(),
            1,
            100,
            (v) => setState(() => hpDrag = v.round()),
            (v) {
              setState(() => hpDrag = null);
              _set(_with(hpPct: v.round()));
            },
            key: 'hp',
          ),
          const SizedBox(height: Space.md),
          Row(
            children: [
              Expanded(
                child: Text('Best balls here', style: AppText.label.copyWith(color: Palette.mutedSlate)),
              ),
              if (odds.isLoading) const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2)),
              const SizedBox(width: Space.xs),
              Text('per throw', style: AppText.label.copyWith(color: Palette.mutedSlate)),
            ],
          ),
          if (odds case AsyncError(:final error) when error is! Unreachable)
            Text('The server had a problem: $error', style: AppText.bodySmall.copyWith(color: Palette.pokeballRedText)),
          for (final b in shown?.balls ?? const <BallOddsOut>[])
            InkWell(
              key: Key('ball-${b.id}'),
              onTap: () => setState(() => ball = b.id),
              child: Container(
                padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 6),
                decoration: BoxDecoration(
                  color: b.id == top?.id ? Palette.insetGray : null,
                  borderRadius: BorderRadius.circular(Radii.inset),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(b.name, style: AppText.bodySmall.copyWith(fontWeight: FontWeight.w700)),
                          Text(b.why, style: AppText.bodySmall.copyWith(color: Palette.inkDim, fontSize: 12)),
                        ],
                      ),
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text('${pctText(b.p)}%', style: AppText.readout.copyWith(fontSize: 15, color: _tone(b.p))),
                        if (!b.sure && b.throws != null)
                          Text('${b.throws} for 90%', style: AppText.readout.copyWith(fontSize: 10, color: Palette.mutedSlate)),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          const SizedBox(height: Space.sm),
          // The rest of the situation, folded away as on the website's tile.
          ExpansionTile(
            key: const Key('situation'),
            tilePadding: EdgeInsets.zero,
            title: Text(
              'Situation: ${['Lv ${q.level}', 'turn ${q.turn}', if (q.night) 'night', if (q.water) 'water', if (q.caught) 'caught'].join(' · ')}',
              style: AppText.bodySmall.copyWith(fontWeight: FontWeight.w600),
            ),
            children: [
              _slider('Wild level', 'Lv ${q.level}', q.level.toDouble(), 1, 100, (v) => _set(_with(level: v.round())), null, key: 'level'),
              _slider(
                'Your level',
                'Lv ${q.myLevel}',
                q.myLevel.toDouble(),
                1,
                100,
                (v) => _set(_with(myLevel: v.round())),
                null,
                key: 'my-level',
              ),
              _slider('Turn', '${q.turn}', q.turn.toDouble(), 1, 30, (v) => _set(_with(turn: v.round())), null, key: 'turn'),
              _slider(
                'Species caught',
                '${q.dexCaught}',
                q.dexCaught.toDouble(),
                0,
                1025,
                (v) => _set(_with(dexCaught: v.round())),
                null,
                key: 'dex',
              ),
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: [
                  _flag('night', 'Night / cave', q.night, (v) => _set(_with(night: v))),
                  _flag('water', 'Fishing / surfing', q.water, (v) => _set(_with(water: v))),
                  _flag('caught', 'Caught before', q.caught, (v) => _set(_with(caught: v))),
                  _flag('love', 'Lead: same species, other gender', q.loveMatch, (v) => _set(_with(loveMatch: v))),
                  _flag('charm', 'Catching Charm', q.charm, (v) => _set(_with(charm: v))),
                ],
              ),
            ],
          ),
          if (top != null) ...[const SizedBox(height: Space.md), _math(top)],
        ],
      ),
    );
  }

  Color _tone(num p) => p > 0.5
      ? Palette.verdictGreenText
      : p > 0.2
      ? Palette.cautionAmberText
      : Palette.pokeballRedText;

  Widget _slider(
    String label,
    String value,
    double v,
    double min,
    double max,
    ValueChanged<double> onChanged,
    ValueChanged<double>? onEnd, {
    required String key,
  }) => Row(
    children: [
      SizedBox(
        width: 92,
        child: Text(label, style: AppText.bodySmall.copyWith(color: Palette.mutedSlate)),
      ),
      Expanded(
        child: Slider(
          key: Key('slider-$key'),
          value: v.clamp(min, max),
          min: min,
          max: max,
          divisions: (max - min).round(),
          // Without onEnd every step asks the server (cheap on the home network).
          onChanged: onChanged,
          onChangeEnd: onEnd,
        ),
      ),
      SizedBox(
        width: 104,
        child: Text(value, textAlign: TextAlign.right, style: AppText.readout.copyWith(fontSize: 12)),
      ),
    ],
  );

  Widget _flag(String key, String label, bool on, ValueChanged<bool> set) =>
      FilterChip(key: Key('flag-$key'), label: Text(label), selected: on, onSelected: set);

  /// The top (or picked) ball's formula, as the website's "math" line.
  Widget _math(BallOddsOut b) {
    final t = b.terms;
    String x(num n) => n % 1 == 0 ? '${n.toInt()}' : n.toStringAsFixed(2).replaceFirst(RegExp(r'0$'), '');
    final head =
        'a = (3·${t.maxHp} − 2·${t.hp}) / (3·${t.maxHp}) × ${t.rate} rate × ${x(t.ball)} ${b.name} × ${x(t.status)} '
        '${q.status == Status.none ? 'healthy' : q.status.json}${t.lowLevel > 1 ? ' × ${x(t.lowLevel)} low Lv' : ''} = ${t.a.toStringAsFixed(1)}';
    final tail = b.sure
        ? ' → guaranteed'
        : ' · shake = 65536 / (255/a)^(3/16) ÷ 65536 = ${t.shake.toStringAsFixed(3)} → '
              '${t.crit > 0 ? 'crit ${(t.crit * 100).toStringAsFixed(1)}% + ' : ''}${t.shake.toStringAsFixed(3)}⁴ = ${pctText(b.p)}%';
    return Container(
      key: const Key('catch-math'),
      padding: const EdgeInsets.all(Space.sm),
      decoration: BoxDecoration(color: Palette.insetGray, borderRadius: BorderRadius.circular(Radii.inset)),
      child: Text(
        '$head$tail\nSword/Shield formula; ball and status multipliers are Gen 5+ values.',
        style: AppText.readout.copyWith(fontSize: 11, height: 1.5),
      ),
    );
  }
}
