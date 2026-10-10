import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/export.dart';
import '../../data/server.dart';
import '../../data/sprites.dart';
import '../../theme/theme.dart';
import '../../theme/tokens.g.dart';
import '../../widgets/artwork.dart';

/// An answer laid out like the website's (`AskConsole`): the first paragraph is the
/// verdict (large, display face, bold in red), later paragraphs are quieter, and "- "
/// bullets become rows that lead with the Pokémon's artwork when a source names it.
/// [n] / 【n】 citations are small red chips that call [onCite]. A leading "*Note: …*"
/// (what the plan couldn't filter by) is an amber notice, never the verdict.
/// Ask and both coaches share it, so every answer reads the same.
class AnswerText extends ConsumerStatefulWidget {
  const AnswerText(this.text, {super.key, required this.onCite, this.sources = const [], this.muted = false});

  final String text;
  final void Function(int n) onCite;
  final List<Source> sources;

  /// The answer abstained: the verdict reads muted.
  final bool muted;

  @override
  ConsumerState<AnswerText> createState() => _AnswerTextState();
}

class _AnswerTextState extends ConsumerState<AnswerText> {
  final _recognizers = <TapGestureRecognizer>[];

  @override
  void dispose() {
    for (final r in _recognizers) {
      r.dispose();
    }
    super.dispose();
  }

  static final _token = RegExp(r'\*\*(.+?)\*\*|[\[【](\d+)[\]】]');
  static final _note = RegExp(r'^\*Note: [\s\S]+\*$');

  List<InlineSpan> _inline(String line, {Color? bold}) {
    final out = <InlineSpan>[];
    var at = 0;
    for (final m in _token.allMatches(line)) {
      if (m.start > at) out.add(TextSpan(text: line.substring(at, m.start)));
      if (m[1] != null) {
        out.add(TextSpan(text: m[1], style: TextStyle(fontWeight: FontWeight.w700, color: bold ?? Palette.instrumentInk)));
      } else {
        final n = int.parse(m[2]!);
        out.add(WidgetSpan(alignment: PlaceholderAlignment.middle, child: _Cite(n: n, onTap: () => widget.onCite(n))));
      }
      at = m.end;
    }
    if (at < line.length) out.add(TextSpan(text: line.substring(at)));
    return out;
  }

  /// The bold label a bullet starts with ("**Garchomp** — …" → garchomp).
  static String? _label(String li) => RegExp(r'^\*\*([^*]+)\*\*').firstMatch(li)?[1]?.replaceAll(RegExp(r'[:\s]+$'), '').toLowerCase();

  @override
  Widget build(BuildContext context) {
    final base = ref.watch(serverAddressProvider);
    final byName = {for (final s in widget.sources) if (s.pokemonName != null) s.pokemonName!.toLowerCase(): s};
    final lines = widget.text.split('\n').map((l) => l.trim()).where((l) => l.isNotEmpty).toList();
    final hasNote = lines.isNotEmpty && _note.hasMatch(lines.first);
    final verdictAt = hasNote ? 1 : 0;
    final out = <Widget>[];
    for (final (i, l) in lines.indexed) {
      if (i == 0 && hasNote) {
        out.add(Container(
          key: const Key('answer-note'),
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(
            color: const Color(0x1AF0B429),
            border: Border.all(color: const Color(0x73F0B429)),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Text(l.replaceAll(RegExp(r'^\*|\*$'), ''), style: AppText.bodySmall.copyWith(color: Palette.instrumentInk)),
        ));
      } else if (l.startsWith('- ')) {
        final li = l.substring(2);
        final label = _label(li);
        final src = label == null ? null : byName[label];
        final id = src?.pokemonId ?? src?.dexNumber;
        out.add(Padding(
          padding: const EdgeInsets.symmetric(vertical: 6),
          child: Row(crossAxisAlignment: id != null ? CrossAxisAlignment.center : CrossAxisAlignment.start, children: [
            if (id != null)
              SizedBox(width: 40, height: 40, child: Artwork(thumbUrl(base, '/sprites/official-artwork/$id.png'), size: 40))
            else
              Container(
                width: 6,
                height: 6,
                margin: const EdgeInsets.fromLTRB(4, 8, 4, 0),
                decoration: const BoxDecoration(color: Palette.pokeballRed, shape: BoxShape.circle),
              ),
            const SizedBox(width: 12),
            Expanded(child: Text.rich(TextSpan(style: AppText.body.copyWith(color: Palette.inkDim), children: _inline(li)))),
          ]),
        ));
      } else if (i == verdictAt) {
        out.add(Text.rich(
          key: const Key('answer-verdict'),
          TextSpan(
            style: AppText.display.copyWith(
              fontSize: 20,
              height: 1.3,
              letterSpacing: -.2,
              color: widget.muted ? Palette.mutedSlate : Palette.instrumentInk,
            ),
            children: _inline(l, bold: Palette.pokeballRedText),
          ),
        ));
      } else {
        out.add(Padding(
          padding: EdgeInsets.only(top: i == 0 ? 0 : 10),
          child: Text.rich(TextSpan(style: AppText.body.copyWith(color: Palette.inkDim), children: _inline(l))),
        ));
      }
    }
    // A list right after the verdict breathes a little.
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      for (final (i, w) in out.indexed) ...[
        if (i > 0 && i - 1 == verdictAt) const SizedBox(height: 8),
        w,
      ],
    ]);
  }
}

/// A citation chip: the source number on a soft red ground (the website's `.ax-cite`).
class _Cite extends StatelessWidget {
  const _Cite({required this.n, required this.onTap});

  final int n;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Semantics(
    button: true,
    label: 'source $n',
    excludeSemantics: true,
    child: GestureDetector(
      key: Key('cite-$n'),
      onTap: onTap,
      // Sized to its number: no alignment, which would stretch it across the line.
      child: Container(
        margin: const EdgeInsets.only(left: 4),
        constraints: const BoxConstraints(minWidth: 20, minHeight: 20),
        padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 3),
        decoration: BoxDecoration(
          color: const Color(0x1FE3350D),
          border: Border.all(color: const Color(0x59D8310C)),
          borderRadius: BorderRadius.circular(6),
        ),
        child: Text('$n', textAlign: TextAlign.center, style: AppText.readout.copyWith(fontSize: 11, height: 1.1, color: Palette.pokeballRedText)),
      ),
    ),
  );
}
