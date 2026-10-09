import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../api/export.dart';
import '../../theme/theme.dart';
import '../../theme/tokens.g.dart';
import 'ask_state.dart';

/// A cited record: its text and, for a Pokémon, a link to its page.
void showSourceSheet(BuildContext context, Source s) => showModalBottomSheet<void>(
      context: context,
      useRootNavigator: true,
      showDragHandle: true,
      isScrollControlled: true,
      builder: (sheet) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(Space.gutter, 0, Space.gutter, Space.gutter * 2),
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('[${s.n}] ${s.pokemonName ?? s.chunkType.replaceAll('_', ' ')}', key: const Key('source-title'), style: AppText.headline),
            Text(s.chunkType.replaceAll('_', ' '), style: AppText.readout.copyWith(color: Palette.mutedSlate)),
            const SizedBox(height: Space.sm),
            Flexible(child: SingleChildScrollView(child: Text(s.snippet, key: const Key('source-snippet'), style: AppText.body))),
            if (s.dexNumber != null) ...[
              const SizedBox(height: Space.md),
              FilledButton(
                key: const Key('source-open'),
                onPressed: () {
                  Navigator.of(sheet).pop();
                  context.push('/pokemon/${s.dexNumber}');
                },
                child: Text('Open ${s.pokemonName ?? 'Pokémon'}'),
              ),
            ],
          ]),
        ),
      ),
    );

/// "Planned by keywords · 0.4 s · 0 LLM calls · 2 lookups"; tap for each step.
class HowAnswered extends StatelessWidget {
  const HowAnswered({super.key, required this.run});

  final AskState run;

  @override
  Widget build(BuildContext context) {
    final lookups = run.steps.length;
    final llm = run.usage['llm_calls'] ?? 0;
    final planner = run.planner == 'llm' ? 'the LLM' : 'keywords';
    return InkWell(
      key: const Key('how-answered'),
      onTap: lookups == 0 ? null : () => _showSteps(context),
      child: Text(
        [
          run.cached ? 'Cached answer' : 'Planned by $planner',
          if (run.elapsed != null) '${(run.elapsed!.inMilliseconds / 1000).toStringAsFixed(1)} s',
          if (run.status == AskStatus.done) '$llm LLM call${llm == 1 ? '' : 's'}',
          '$lookups lookup${lookups == 1 ? '' : 's'}',
        ].join(' · '),
        style: AppText.readout.copyWith(fontSize: 11, color: Palette.mutedSlate),
      ),
    );
  }

  void _showSteps(BuildContext context) => showModalBottomSheet<void>(
        context: context,
        useRootNavigator: true,
        showDragHandle: true,
        builder: (_) => SafeArea(
          child: ListView(
            shrinkWrap: true,
            padding: const EdgeInsets.fromLTRB(Space.gutter, 0, Space.gutter, Space.gutter * 2),
            children: [
              Text('How it was answered', style: AppText.headline),
              for (final s in run.steps)
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: Icon(
                    switch (s.state) {
                      'done' => Icons.check_circle_outline,
                      'error' => Icons.error_outline,
                      'empty' => Icons.remove_circle_outline,
                      _ => Icons.more_horiz,
                    },
                    color: s.state == 'error' ? Palette.pokeballRed : Palette.inkDim,
                  ),
                  title: Text('${s.tool}${s.replan ? ' · follow-up' : ''}', style: AppText.readout),
                  subtitle: Text([s.why, if (s.summary.isNotEmpty) s.summary].join('\n'), style: AppText.bodySmall),
                ),
            ],
          ),
        ),
      );
}

/// What's happening while the answer hasn't started: planning, a lookup, or writing.
String runningLine(AskState run) {
  final running = run.steps.where((s) => s.state == 'running').firstOrNull;
  if (running != null) return 'Looking up: ${running.why}…';
  if (run.steps.isEmpty) return 'Planning…';
  return 'Writing the answer…';
}
