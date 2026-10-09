// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'type_chart_view.g.dart';

/// How one type (or a dual typing) fares defensively.
@JsonSerializable()
class TypeChartView {
  const TypeChartView({
    required this.types,
    this.kind = 'type_chart',
    this.chunkRefs,
    this.immune,
    this.resistHalf,
    this.resistQuarter,
    this.step,
    this.strongAgainst,
    this.weak2x,
    this.weak4x,
  });
  
  factory TypeChartView.fromJson(Map<String, Object?> json) => _$TypeChartViewFromJson(json);
  
  @JsonKey(name: 'chunk_refs')
  final List<int>? chunkRefs;
  final List<String>? immune;
  final String kind;
  @JsonKey(name: 'resist_half')
  final List<String>? resistHalf;
  @JsonKey(name: 'resist_quarter')
  final List<String>? resistQuarter;
  final String? step;
  @JsonKey(name: 'strong_against')
  final List<String>? strongAgainst;
  final List<String> types;
  @JsonKey(name: 'weak_2x')
  final List<String>? weak2x;
  @JsonKey(name: 'weak_4x')
  final List<String>? weak4x;

  Map<String, Object?> toJson() => _$TypeChartViewToJson(this);
}
