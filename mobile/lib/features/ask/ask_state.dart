import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/export.dart';
import '../../data/errors.dart';
import '../../data/pokedex_repository.dart' show failureOf;
import '../../data/server.dart';
import 'sse.dart';
import 'views.dart';

enum AskStatus { idle, streaming, done, error }

/// One plan step as the stream reports it (the envelope; payloads are generated types).
class AskStep {
  const AskStep({required this.id, required this.tool, required this.why, this.state = 'pending', this.summary = '', this.replan = false});
  final String id;
  final String tool;
  final String why;
  final String state; // pending | running | done | empty | error
  final String summary;
  final bool replan;

  AskStep copyWith({String? state, String? summary}) =>
      AskStep(id: id, tool: tool, why: why, state: state ?? this.state, summary: summary ?? this.summary, replan: replan);
}

class AskState {
  const AskState({
    this.question = '',
    this.status = AskStatus.idle,
    this.planner,
    this.cached = false,
    this.steps = const [],
    this.views = const [],
    this.sources = const [],
    this.answer = '',
    this.unhandled = const [],
    this.usage = const {},
    this.elapsed,
    this.error,
    this.errorMessage,
  });

  final String question;
  final AskStatus status;
  final String? planner;
  final bool cached;
  final List<AskStep> steps;
  final List<Object> views; // generated view classes (see views.dart)
  final List<Source> sources;
  final String answer;
  final List<String> unhandled;
  final Map<String, int> usage;
  final Duration? elapsed;
  final Object? error;

  /// The stream's own error text, when the server reported one (`error` event).
  final String? errorMessage;

  AskState copyWith({
    AskStatus? status,
    String? planner,
    bool? cached,
    List<AskStep>? steps,
    List<Object>? views,
    List<Source>? sources,
    String? answer,
    List<String>? unhandled,
    Map<String, int>? usage,
    Duration? elapsed,
    Object? error,
    String? errorMessage,
  }) =>
      AskState(
        question: question,
        status: status ?? this.status,
        planner: planner ?? this.planner,
        cached: cached ?? this.cached,
        steps: steps ?? this.steps,
        views: views ?? this.views,
        sources: sources ?? this.sources,
        answer: answer ?? this.answer,
        unhandled: unhandled ?? this.unhandled,
        usage: usage ?? this.usage,
        elapsed: elapsed ?? this.elapsed,
        error: error ?? this.error,
        errorMessage: errorMessage ?? this.errorMessage,
      );
}

final askProvider = NotifierProvider<AskRun, AskState>(AskRun.new);

/// Streams one question at a time from /api/ask/stream; a new question cancels the last.
class AskRun extends Notifier<AskState> {
  CancelToken? _cancel;

  @override
  AskState build() {
    ref.onDispose(() => _cancel?.cancel());
    return const AskState();
  }

  Future<void> ask(String question) async {
    final q = question.trim();
    if (q.isEmpty) return;
    _cancel?.cancel();
    final cancel = _cancel = CancelToken();
    state = AskState(question: q, status: AskStatus.streaming);
    final started = DateTime.now();
    final dio = ref.read(dioProvider);
    try {
      final res = await dio.post<ResponseBody>(
        '/api/ask/stream',
        data: {'question': q},
        cancelToken: cancel,
        options: Options(responseType: ResponseType.stream, receiveTimeout: const Duration(minutes: 2)),
      );
      await for (final e in parseSse(res.data!.stream)) {
        if (cancel.isCancelled) return;
        _apply(e);
      }
      if (cancel.isCancelled) return;
      if (state.status == AskStatus.streaming) state = state.copyWith(status: AskStatus.done);
    } on DioException catch (e) {
      if (CancelToken.isCancel(e)) return;
      state = state.copyWith(status: AskStatus.error, error: failureOf(e, dio.options.baseUrl));
    } catch (e) {
      state = state.copyWith(status: AskStatus.error, error: e);
    } finally {
      if (identical(_cancel, cancel)) state = state.copyWith(elapsed: DateTime.now().difference(started));
    }
  }

  void _apply(SseEvent e) {
    final d = e.data;
    switch (e.name) {
      case 'plan':
        final m = d! as Map;
        final replan = m['replan'] == true;
        final steps = [
          for (final s in (m['steps'] as List).cast<Map>())
            AskStep(
              id: '${s['id']}',
              tool: '${s['tool']}',
              why: '${s['why'] ?? ''}',
              state: s['error'] != null ? 'error' : 'pending',
              summary: '${s['error'] ?? ''}',
              replan: replan,
            ),
        ];
        state = state.copyWith(
          planner: replan ? null : '${m['planner']}',
          cached: replan ? null : m['cached'] == true,
          steps: [...state.steps, ...steps],
          unhandled: replan ? null : [for (final u in (m['unhandled'] as List? ?? const [])) '$u'],
        );
      case 'step':
        final m = d! as Map;
        state = state.copyWith(steps: [
          for (final s in state.steps) s.id == m['id'] ? s.copyWith(state: '${m['state']}', summary: '${m['summary'] ?? ''}') : s,
        ]);
      case 'view':
        // A view kind this app doesn't draw decodes to null: skip it, keep the answer.
        final v = decodeView(Map<String, dynamic>.from(d! as Map));
        if (v != null) state = state.copyWith(views: [...state.views, v]);
      case 'sources':
        state = state.copyWith(sources: [for (final s in (d! as List)) Source.fromJson(Map<String, dynamic>.from(s as Map))]);
      case 'delta':
        state = state.copyWith(answer: '${state.answer}${(d! as Map)['text']}');
      case 'done':
        final usage = ((d as Map?)?['usage'] as Map?) ?? const {};
        state = state.copyWith(status: AskStatus.done, usage: {for (final e in usage.entries) '${e.key}': (e.value as num).toInt()});
      case 'error':
        state = state.copyWith(
          status: AskStatus.error,
          error: const ServerError(null),
          errorMessage: '${(d as Map?)?['message'] ?? 'The server failed to answer.'}',
        );
    }
  }
}

/// LLM status for the tab ("LLM" or keyless).
/// (The endpoint declares no response model, so its two fields are read here.)
final askStatusProvider = FutureProvider<({bool enabled, String provider})>((ref) async {
  try {
    final m = await PokeragClient(ref.watch(dioProvider)).askStatusApiAskStatusGet() as Map;
    return (enabled: m['enabled'] == true, provider: '${m['provider'] ?? 'none'}');
  } on DioException catch (e) {
    throw failureOf(e, ref.read(dioProvider).options.baseUrl);
  }
});

/// What a cited source is, for the citation sheet.
Source? sourceOf(AskState s, int n) => s.sources.where((x) => x.n == n).firstOrNull;

/// Unreachable is shown as the can't-reach state; anything else as an error line.
bool isUnreachable(Object? e) => e is Unreachable;
