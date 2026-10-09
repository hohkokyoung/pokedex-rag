// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'type_chart_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TypeChartOut _$TypeChartOutFromJson(Map<String, dynamic> json) => TypeChartOut(
  chart: (json['chart'] as Map<String, dynamic>).map(
    (k, e) => MapEntry(k, Map<String, num>.from(e as Map)),
  ),
  order: (json['order'] as List<dynamic>).map((e) => e as String).toList(),
);

Map<String, dynamic> _$TypeChartOutToJson(TypeChartOut instance) =>
    <String, dynamic>{'chart': instance.chart, 'order': instance.order};
