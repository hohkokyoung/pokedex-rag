// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'nature_out.g.dart';

@JsonSerializable()
class NatureOut {
  const NatureOut({
    required this.id,
    required this.identifier,
    required this.name,
    this.decreasedStat,
    this.increasedStat,
  });
  
  factory NatureOut.fromJson(Map<String, Object?> json) => _$NatureOutFromJson(json);
  
  @JsonKey(name: 'decreased_stat')
  final String? decreasedStat;
  final int id;
  final String identifier;
  @JsonKey(name: 'increased_stat')
  final String? increasedStat;
  final String name;

  Map<String, Object?> toJson() => _$NatureOutToJson(this);
}
