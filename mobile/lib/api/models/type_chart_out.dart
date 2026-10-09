// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'type_chart_out.g.dart';

/// The 18 battle types in display order and every attacking → defending multiplier.
@JsonSerializable()
class TypeChartOut {
  const TypeChartOut({
    required this.chart,
    required this.order,
  });
  
  factory TypeChartOut.fromJson(Map<String, Object?> json) => _$TypeChartOutFromJson(json);
  
  final Map<String, Map<String, num>> chart;
  final List<String> order;

  Map<String, Object?> toJson() => _$TypeChartOutToJson(this);
}
