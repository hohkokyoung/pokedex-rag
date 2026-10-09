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
    await streamAsk(ref.read(dioProvider), '/api/ask/stream', {'question': q}, cancel,
        read: () => state, emit: (s) => state = s);
  }
}

/// Streams an Ask-shaped SSE answer (Ask or the team coach) into [emit], starting from
/// a fresh streaming state for the question in [body]. Events other than Ask's go to
/// [onOther] (e.g. the coach's `team_updated`). Stops quietly once [cancel] fires.
Future<void> streamAsk(
  Dio dio,
  String path,
  Map<String, Object?> body,
  CancelToken cancel, {
  required AskState Function() read,
  required void Function(AskState) emit,
  void Function(SseEvent e)? onOther,
}) async {
  emit(AskState(question: '${body['question']}', status: AskStatus.streaming));
  final started = DateTime.now();
  try {
    final res = await dio.post<ResponseBody>(
      path,
      data: body,
      cancelToken: cancel,
      options: Options(responseType: ResponseType.stream, receiveTimeout: const Duration(minutes: 2)),
    );
    await for (final e in parseSse(res.data!.stream)) {
      if (cancel.isCancelled) return;
      final next = applyAskEvent(read(), e);
      if (next == null) {
        onOther?.call(e);
      } else {
        emit(next);
      }
    }
    if (cancel.isCancelled) return;
    if (read().status == AskStatus.streaming) emit(read().copyWith(status: AskStatus.done));
  } on DioException catch (e) {
    if (CancelToken.isCancel(e)) return;
    emit(read().copyWith(status: AskStatus.error, error: failureOf(e, dio.options.baseUrl)));
  } catch (e) {
    emit(read().copyWith(status: AskStatus.error, error: e));
  } finally {
    if (!cancel.isCancelled) emit(read().copyWith(elapsed: DateTime.now().difference(started)));
  }
}

/// One Ask stream event applied to [s]; null for an event that isn't Ask's.
AskState? applyAskEvent(AskState s, SseEvent e) {
  final d = e.data;
  switch (e.name) {
    case 'plan':
      final m = d! as Map;
      final replan = m['replan'] == true;
      final steps = [
        for (final st in (m['steps'] as List).cast<Map>())
          AskStep(
            id: '${st['id']}',
            tool: '${st['tool']}',
            why: '${st['why'] ?? ''}',
            state: st['error'] != null ? 'error' : 'pending',
            summary: '${st['error'] ?? ''}',
            replan: replan,
          ),
      ];
      return s.copyWith(
        planner: replan ? null : '${m['planner']}',
        cached: replan ? null : m['cached'] == true,
        steps: [...s.steps, ...steps],
        unhandled: replan ? null : [for (final u in (m['unhandled'] as List? ?? const [])) '$u'],
      );
    case 'step':
      final m = d! as Map;
      return s.copyWith(steps: [
        for (final st in s.steps) st.id == m['id'] ? st.copyWith(state: '${m['state']}', summary: '${m['summary'] ?? ''}') : st,
      ]);
    case 'view':
      // A view kind this app doesn't draw decodes to null: skip it, keep the answer.
      final v = decodeView(Map<String, dynamic>.from(d! as Map));
      return v == null ? s : s.copyWith(views: [...s.views, v]);
    case 'sources':
      return s.copyWith(sources: [for (final x in (d! as List)) Source.fromJson(Map<String, dynamic>.from(x as Map))]);
    case 'delta':
      return s.copyWith(answer: '${s.answer}${(d! as Map)['text']}');
    case 'done':
      final usage = ((d as Map?)?['usage'] as Map?) ?? const {};
      return s.copyWith(status: AskStatus.done, usage: {for (final u in usage.entries) '${u.key}': (u.value as num).toInt()});
    case 'error':
      return s.copyWith(
        status: AskStatus.error,
        error: const ServerError(null),
        errorMessage: '${(d as Map?)?['message'] ?? 'The server failed to answer.'}',
      );
  }
  return null;
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
