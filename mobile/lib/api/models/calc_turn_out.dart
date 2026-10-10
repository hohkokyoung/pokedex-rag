// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'calc_hp_out.dart';
import 'calc_move_out.dart';
import 'calc_order_out.dart';
import 'calc_step_out.dart';

part 'calc_turn_out.g.dart';

@JsonSerializable()
class CalcTurnOut {
  const CalcTurnOut({
    required this.aims,
    required this.hp,
    required this.moves,
    required this.order,
    required this.steps,
  });
  
  factory CalcTurnOut.fromJson(Map<String, Object?> json) => _$CalcTurnOutFromJson(json);
  
  final Map<String, int?> aims;
  final List<CalcHpOut> hp;
  final List<CalcMoveOut> moves;
  final List<CalcOrderOut> order;
  final List<CalcStepOut> steps;

  Map<String, Object?> toJson() => _$CalcTurnOutToJson(this);
}
