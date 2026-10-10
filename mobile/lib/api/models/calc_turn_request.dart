// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'calc_field.dart';
import 'calc_slot.dart';

part 'calc_turn_request.g.dart';

/// The calculator's state, to play one turn (``POST /api/calc/turn``).
@JsonSerializable()
class CalcTurnRequest {
  const CalcTurnRequest({
    this.field,
    this.slots,
    this.doubles = false,
    this.level = 100,
  });
  
  factory CalcTurnRequest.fromJson(Map<String, Object?> json) => _$CalcTurnRequestFromJson(json);
  
  final bool doubles;
  final CalcField? field;
  final int level;
  final List<CalcSlot>? slots;

  Map<String, Object?> toJson() => _$CalcTurnRequestToJson(this);
}
