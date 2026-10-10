// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'calc_option_out.dart';

part 'calc_options_out.g.dart';

/// What the damage maths models, for the calculator's pickers.
@JsonSerializable()
class CalcOptionsOut {
  const CalcOptionsOut({
    required this.abilities,
    required this.items,
    required this.natures,
    required this.terrains,
    required this.weathers,
  });
  
  factory CalcOptionsOut.fromJson(Map<String, Object?> json) => _$CalcOptionsOutFromJson(json);
  
  final List<CalcOptionOut> abilities;
  final List<CalcOptionOut> items;
  final List<String> natures;
  final List<String> terrains;
  final List<String> weathers;

  Map<String, Object?> toJson() => _$CalcOptionsOutToJson(this);
}
