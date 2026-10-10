// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'calc_option_out_side.dart';

part 'calc_option_out.g.dart';

@JsonSerializable()
class CalcOptionOut {
  const CalcOptionOut({
    required this.name,
    required this.note,
    required this.side,
  });
  
  factory CalcOptionOut.fromJson(Map<String, Object?> json) => _$CalcOptionOutFromJson(json);
  
  final String name;
  final String note;
  final CalcOptionOutSide side;

  Map<String, Object?> toJson() => _$CalcOptionOutToJson(this);
}
