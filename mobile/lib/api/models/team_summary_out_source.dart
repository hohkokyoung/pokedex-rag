// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

@JsonEnum()
enum TeamSummaryOutSource {
  @JsonValue('ai')
  ai('ai'),
  @JsonValue('rules')
  rules('rules'),
  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const TeamSummaryOutSource(this.json);

  factory TeamSummaryOutSource.fromJson(String json) => values.firstWhere(
        (e) => e.json == json,
        orElse: () => $unknown,
      );

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();
  /// Returns all defined enum values excluding the $unknown value.
  static List<TeamSummaryOutSource> get $valuesDefined => values.where((value) => value != $unknown).toList();
}
