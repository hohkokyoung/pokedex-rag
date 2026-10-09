import 'dart:convert';

/// One Server-Sent Event: `event: <name>` + `data: <json>`.
class SseEvent {
  const SseEvent(this.name, this.data);
  final String name;
  final Object? data;
}

/// Splits a text/event-stream byte stream into events (frames end with a blank line).
Stream<SseEvent> parseSse(Stream<List<int>> bytes) async* {
  String? name;
  final data = StringBuffer();
  await for (final line in const LineSplitter().bind(utf8.decoder.bind(bytes))) {
    if (line.isEmpty) {
      if (name != null || data.isNotEmpty) {
        final text = data.toString();
        yield SseEvent(name ?? 'message', text.isEmpty ? null : jsonDecode(text));
      }
      name = null;
      data.clear();
    } else if (line.startsWith('event:')) {
      name = line.substring(6).trim();
    } else if (line.startsWith('data:')) {
      if (data.isNotEmpty) data.write('\n');
      data.write(line.substring(5).trimLeft());
    }
  }
  if (name != null || data.isNotEmpty) {
    final text = data.toString();
    yield SseEvent(name ?? 'message', text.isEmpty ? null : jsonDecode(text));
  }
}
