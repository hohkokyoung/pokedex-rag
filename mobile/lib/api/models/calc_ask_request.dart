// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'calc_field.dart';
import 'calc_hit_in.dart';
import 'calc_proposal.dart';
import 'calc_slot.dart';

part 'calc_ask_request.g.dart';

@JsonSerializable()
class CalcAskRequest {
  const CalcAskRequest({
    required this.question,
    this.field,
    this.hits,
    this.proposal,
    this.slots,
    this.doubles = false,
    this.focus = 0,
    this.level = 100,
  });
  
  factory CalcAskRequest.fromJson(Map<String, Object?> json) => _$CalcAskRequestFromJson(json);
  
  final bool doubles;
  final CalcField? field;
  final int focus;
  final List<CalcHitIn>? hits;
  final int level;
  final CalcProposal? proposal;
  final String question;
  final List<CalcSlot>? slots;

  Map<String, Object?> toJson() => _$CalcAskRequestToJson(this);
}
