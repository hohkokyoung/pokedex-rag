import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'pokedex_repository.dart';

/// The build's default server: `--dart-define=API_BASE_URL=...` (the Make targets set
/// it); `localhost` reaches the Mac from the iOS Simulator.
const defaultAddress = String.fromEnvironment('API_BASE_URL', defaultValue: 'http://localhost:8001');

const _key = 'server_address';

/// Device storage, opened before the app starts (overridden in `main` and in tests).
final prefsProvider = Provider<SharedPreferences>((ref) => throw UnimplementedError('override in main'));

/// Lets tests swap the network for a fake backend; null means the real network.
final httpAdapterProvider = Provider<HttpClientAdapter?>((ref) => null);

/// The server the app reads from: the saved address, else the build default.
final serverAddressProvider = NotifierProvider<ServerAddress, String>(ServerAddress.new);

class ServerAddress extends Notifier<String> {
  @override
  String build() => ref.watch(prefsProvider).getString(_key) ?? defaultAddress;

  /// Checks [input] is a pokérag server, then saves it. Returns why it wasn't saved,
  /// or null when it was.
  Future<String?> save(String input) async {
    final address = normalize(input);
    if (address == null) return 'Enter an address like http://192.168.0.10:8001';
    final problem = await checkServer(address, adapter: ref.read(httpAdapterProvider));
    if (problem != null) return problem;
    await ref.read(prefsProvider).setString(_key, address);
    state = address;
    return null;
  }

  /// Back to the build default.
  Future<void> reset() async {
    await ref.read(prefsProvider).remove(_key);
    state = defaultAddress;
  }
}

/// `192.168.0.10:8001` → `http://192.168.0.10:8001`; null when it isn't a usable URL.
String? normalize(String input) {
  var s = input.trim();
  if (s.isEmpty) return null;
  if (!s.contains('://')) s = 'http://$s';
  final uri = Uri.tryParse(s);
  if (uri == null || !uri.hasAuthority || !(uri.scheme == 'http' || uri.scheme == 'https')) return null;
  // A host name or IPv4 address (Uri.tryParse alone accepts "not a url" as a host).
  if (!RegExp(r'^[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?$').hasMatch(uri.host)) return null;
  return uri.replace(path: '', query: null, fragment: null).toString().replaceAll(RegExp(r'[/?#]+$'), '');
}

/// Asks `[address]/health` whether a pokérag server is there (3 s). Returns null when
/// it is, else a sentence for the user.
Future<String?> checkServer(String address, {HttpClientAdapter? adapter}) async {
  final dio = _dio(address, adapter, timeout: const Duration(seconds: 3));
  try {
    final r = await dio.get<Object?>('/health');
    final body = r.data;
    if (body is Map && body['status'] == 'ok') return null;
    return 'Something answered at $address, but it isn\'t a pokérag server.';
  } on DioException catch (e) {
    if (e.response != null) return 'Something answered at $address, but it isn\'t a pokérag server.';
    return "Couldn't reach a pokérag server at $address. Check the address, and that your phone is on the same Wi-Fi.";
  } finally {
    dio.close();
  }
}

Dio _dio(String address, HttpClientAdapter? adapter, {Duration timeout = const Duration(seconds: 5)}) {
  final dio = Dio(BaseOptions(baseUrl: address, connectTimeout: timeout, receiveTimeout: const Duration(seconds: 15)));
  if (adapter != null) dio.httpClientAdapter = adapter;
  return dio;
}

/// The repository for the current server. A new address gets a new repository, so the
/// type chart is fetched again for it.
final repositoryProvider = Provider<PokedexRepository>((ref) {
  final dio = _dio(ref.watch(serverAddressProvider), ref.watch(httpAdapterProvider));
  ref.onDispose(dio.close);
  return PokedexRepository(dio);
});
