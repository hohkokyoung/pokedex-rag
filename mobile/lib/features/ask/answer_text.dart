import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';

import '../../theme/theme.dart';
import '../../theme/tokens.g.dart';

/// Renders an answer's light markdown: paragraphs, "- " bullets, **bold**, and [n] / 【n】
/// citations that call [onCite].
class AnswerText extends StatefulWidget {
  const AnswerText(this.text, {super.key, required this.onCite});

  final String text;
  final void Function(int n) onCite;

  @override
  State<AnswerText> createState() => _AnswerTextState();
}

class _AnswerTextState extends State<AnswerText> {
  final _recognizers = <TapGestureRecognizer>[];

  @override
  void dispose() {
    for (final r in _recognizers) {
      r.dispose();
    }
    super.dispose();
  }

  static final _token = RegExp(r'\*\*(.+?)\*\*|[\[【](\d+)[\]】]');

  List<InlineSpan> _inline(String line) {
    final out = <InlineSpan>[];
    var at = 0;
    for (final m in _token.allMatches(line)) {
      if (m.start > at) out.add(TextSpan(text: line.substring(at, m.start)));
      if (m[1] != null) {
        out.add(TextSpan(text: m[1], style: const TextStyle(fontWeight: FontWeight.w700)));
      } else {
        final n = int.parse(m[2]!);
        final r = TapGestureRecognizer()..onTap = () => widget.onCite(n);
        _recognizers.add(r);
        out.add(TextSpan(
          text: '[$n]',
          recognizer: r,
          semanticsLabel: 'source $n',
          style: AppText.readout.copyWith(fontSize: 12, color: Palette.youBlueText),
        ));
      }
      at = m.end;
    }
    if (at < line.length) out.add(TextSpan(text: line.substring(at)));
    return out;
  }

  @override
  Widget build(BuildContext context) {
    for (final r in _recognizers) {
      r.dispose();
    }
    _recognizers.clear();
    final lines = widget.text.split('\n').where((l) => l.trim().isNotEmpty).toList();
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      for (final l in lines)
        Padding(
          padding: const EdgeInsets.only(bottom: 6),
          child: l.trimLeft().startsWith('- ')
              ? Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text('•  ', style: AppText.body.copyWith(color: Palette.mutedSlate)),
                  Expanded(child: Text.rich(TextSpan(style: AppText.body, children: _inline(l.trimLeft().substring(2))))),
                ])
              : Text.rich(TextSpan(style: AppText.body, children: _inline(l))),
        ),
    ]);
  }
}
