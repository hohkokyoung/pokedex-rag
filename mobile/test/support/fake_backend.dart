// A stand-in backend for tests: answers dio requests from recorded fixtures (or a
// handler), counts requests per path, and can play "server down".
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';

Object? fixture(String name) => jsonDecode(File('test/fixtures/$name.json').readAsStringSync());

typedef Handler = Object? Function(RequestOptions o);

class FakeBackend implements HttpClientAdapter {
  FakeBackend(this.handler);

  Handler handler;
  bool down = false;

  /// When set, only these base URLs answer; anything else is "connection refused".
  Set<String>? reachableAt;
  final Map<String, int> hits = {};
  final List<RequestOptions> requests = [];

  Dio dio({String baseUrl = 'http://fake:8001'}) => Dio(BaseOptions(baseUrl: baseUrl))..httpClientAdapter = this;

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<Uint8List>? body, Future<void>? cancel) async {
    if (down || (reachableAt != null && !reachableAt!.contains(o.baseUrl))) {
      throw DioException.connectionError(requestOptions: o, reason: 'Connection refused');
    }
    hits[o.path] = (hits[o.path] ?? 0) + 1;
    requests.add(o);
    final out = handler(o);
    if (out is int) return ResponseBody.fromString('{"detail":"x"}', out, headers: _json);
    return ResponseBody.fromString(jsonEncode(out), 200, headers: _json);
  }

  static final _json = {
    Headers.contentTypeHeader: [Headers.jsonContentType],
  };

  @override
  void close({bool force = false}) {}
}

/// A list endpoint over [total] synthetic Pokémon, paged like the backend.
Map<String, Object?> listPage(RequestOptions o, {int total = 95}) {
  final offset = int.parse('${o.queryParameters['offset'] ?? 0}');
  final limit = int.parse('${o.queryParameters['limit'] ?? 40}');
  final end = (offset + limit).clamp(0, total);
  return {
    'items': [
      for (var i = offset; i < end; i++)
        {
          'id': i + 1,
          'dex_number': i + 1,
          'name': i == 0 ? 'Bulbasaur' : 'Mon${i + 1}',
          'types': ['grass', 'poison'],
          'sprite_url': '/sprites/official-artwork/${i + 1}.png',
          'base_stat_total': 300,
          'generation_id': 1,
          'is_legendary': false,
          'is_mythical': false,
          'form_id': null,
          'stats': {'hp': 1, 'attack': 1, 'defense': 1, 'sp_attack': 1, 'sp_defense': 1, 'speed': 1, 'total': 6},
        },
    ],
    'total': total,
    'limit': limit,
    'offset': offset,
  };
}
