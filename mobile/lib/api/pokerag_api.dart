// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';

import 'clients/pokerag_client.dart';

/// pokérag API `v0.1.0`.
///
/// Backend for the premium Pokédex + personalized RAG project.
class PokeragApi {
  PokeragApi(
    Dio dio, {
    String? baseUrl,
  })  : _dio = dio,
        _baseUrl = baseUrl;

  final Dio _dio;
  final String? _baseUrl;

  static String get version => '0.1.0';

  PokeragClient? _pokerag;

  PokeragClient get pokerag => _pokerag ??= PokeragClient(_dio, baseUrl: _baseUrl);
}
