import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/export.dart';
import '../../data/errors.dart';
import '../../theme/theme.dart';
import '../../theme/tokens.g.dart';
import '../../widgets/ui.dart';
import '../../widgets/cant_reach.dart';
import 'answer_text.dart';
import 'ask_cards.dart';
import 'ask_parts.dart';
import 'ask_state.dart';
import 'profile_sheet.dart';

/// The website's starter questions (AskConsole SUGGESTIONS), labelled by what they exercise.
const starters = [
  ('Rank', 'Which Pokémon has the highest Attack?'),
  ('Lore', 'Which Fire-types live near volcanoes?'),
  ('Multi', 'Which Fire types learn Will-O-Wisp, and what is Fire weak to?'),
  ('Matchup', 'Which special attacker has coverage against Dark?'),
  ('For you', 'Which Pokémon would I probably like?'),
];

/// An answer that says the data can't answer (the website's ABSTAIN).
final abstain = RegExp(r"don.t have (that|anything)", caseSensitive: false);

/// Follow-ups from what was cited (the website's followUps): no LLM, only question
/// shapes the retriever handles reliably.
List<String> followUps(List<Source> cited) {
  final names = <String>[];
  for (final s in cited) {
    if (s.pokemonName != null && !names.contains(s.pokemonName)) names.add(s.pokemonName!);
  }
  if (names.isEmpty) return const [];
  return [
    'Tell me about ${names[0]}',
    'What is similar to ${names[0]}?',
    if (names.length > 1) 'Tell me about ${names[1]}',
  ];
}

bool abstained(AskState run) =>
    run.status == AskStatus.done && abstain.hasMatch(run.answer) && citedNumbers(run.answer).isEmpty;

Set<int> citedNumbers(String answer) => {
  for (final m in RegExp(r'[\[【](\d+)[\]】]').allMatches(answer)) int.parse(m[1]!),
};

class AskScreen extends ConsumerStatefulWidget {
  const AskScreen({super.key});

  @override
  ConsumerState<AskScreen> createState() => _AskScreenState();
}

class _AskScreenState extends ConsumerState<AskScreen> {
  final _field = TextEditingController();

  @override
  void dispose() {
    _field.dispose();
    super.dispose();
  }

  void _ask(String q) {
    if (q.trim().isEmpty) return;
    _field.text = q;
    FocusScope.of(context).unfocus();
    ref.read(askProvider.notifier).ask(q);
  }

  void _cite(int n) {
    final s = sourceOf(ref.read(askProvider), n);
    if (s != null) showSourceSheet(context, s);
  }

  @override
  Widget build(BuildContext context) {
    final run = ref.watch(askProvider);
    final status = ref.watch(askStatusProvider).value;
    final streaming = run.status == AskStatus.streaming;
    final cited = citedNumbers(run.answer);
    final next = run.status == AskStatus.done && !abstained(run)
        ? followUps(run.sources.where((s) => cited.contains(s.n)).toList())
        : const <String>[];
    return Scaffold(
      appBar: pageBar(
        'Ask',
        root: true,
        actions: [
          SquareButton(
            key: const Key('open-profile'),
            tooltip: 'Your profile',
            icon: Icons.person_outline,
            onPressed: () => showProfileSheet(context),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(Space.gutter, 0, Space.gutter, Space.gutter * 3),
        children: [
          TextField(
            key: const Key('ask-field'),
            controller: _field,
            autocorrect: false,
            textInputAction: TextInputAction.send,
            onSubmitted: _ask,
            maxLines: 3,
            minLines: 1,
            decoration: InputDecoration(
              hintText: 'Ask about Pokémon, moves, types…',
              suffixIcon: SendButton(key: const Key('ask-send'), busy: streaming, onPressed: () => _ask(_field.text)),
            ),
          ),
          if (status != null)
            Padding(
              padding: const EdgeInsets.only(top: Space.xs),
              child: Text(
                status.enabled
                    ? 'Answers from your data, narrated by ${status.provider == 'groq'
                          ? 'Groq'
                          : status.provider == 'anthropic'
                          ? 'Claude'
                          : status.provider}.'
                    : 'Keyless: questions are planned by keywords and answers quote the records.',
                key: const Key('ask-status'),
                style: AppText.bodySmall.copyWith(color: Palette.mutedSlate),
              ),
            ),
          const SizedBox(height: Space.sm),
          // Suggestions as one panel of rows (no chip tap-target gaps): the starters
          // before a question, "Ask next" after an answer.
          if (run.status == AskStatus.idle)
            _suggestions(null, [for (final (kind, q) in starters) (Key('starter-$kind'), kind, q)]),
          const SizedBox(height: Space.md),
          ..._result(run),
          // Follow-ups after the answer, as on the website.
          if (next.isNotEmpty) ...[
            const SizedBox(height: Space.md),
            _suggestions('Ask next', [for (final f in next) (Key('next-$f'), null, f)]),
          ],
        ],
      ),
    );
  }

  Widget _suggestions(String? title, List<(Key, String?, String)> rows) =>
      SuggestionRows(title: title, rows: rows, onTap: _ask);

  List<Widget> _result(AskState run) {
    if (run.status == AskStatus.idle) return const [];
    if (run.status == AskStatus.error && run.error is Unreachable) {
      return [CantReach(address: (run.error! as Unreachable).address, onRetry: () => _ask(run.question))];
    }
    return [
      if (run.unhandled.isNotEmpty)
        Padding(
          padding: const EdgeInsets.only(bottom: Space.sm),
          child: Text(
            "Couldn't apply: ${run.unhandled.join(', ')}. The answer below is broader.",
            key: const Key('ask-notice'),
            style: AppText.bodySmall.copyWith(color: Palette.cautionAmberText),
          ),
        ),
      // Verdict first, as on the website: no "Answer" heading over it.
      Card(
        key: const Key('answer'),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(Space.md, Space.md + 2, Space.md, Space.md),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (run.answer.isEmpty && run.status == AskStatus.streaming)
                Text(runningLine(run), style: AppText.bodySmall.copyWith(color: Palette.mutedSlate))
              else if (run.answer.isNotEmpty)
                AnswerText(run.answer, onCite: _cite, sources: run.sources, muted: abstained(run)),
              if (run.status == AskStatus.error && run.answer.isEmpty)
                Text(
                  run.errorMessage ?? 'The server had a problem answering.',
                  key: const Key('ask-error'),
                  style: AppText.body.copyWith(color: Palette.pokeballRedText),
                ),
              const SizedBox(height: Space.md),
              HowAnswered(run: run),
            ],
          ),
        ),
      ),
      for (final v in run.views)
        Padding(
          padding: const EdgeInsets.only(top: Space.md),
          child: ViewCard(view: v, sources: run.sources, onCite: _cite),
        ),
    ];
  }
}
