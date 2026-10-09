// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'calc_ref.g.dart';

@JsonSerializable()
class CalcRef {
  const CalcRef({
    required this.name,
    required this.side,
    required this.slot,
    this.dexNumber,
  });
  
  factory CalcRef.fromJson(Map<String, Object?> json) => _$CalcRefFromJson(json);
  
  @JsonKey(name: 'dex_number')
  final int? dexNumber;
  final String name;
  final int side;
  final int slot;

  Map<String, Object?> toJson() => _$CalcRefToJson(this);
}
