// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'calc_field.g.dart';

@JsonSerializable()
class CalcField {
  const CalcField({
    this.burn = false,
    this.crit = false,
    this.friendGuard = false,
    this.lightscreen = false,
    this.reflect = false,
    this.terrain = 'None',
    this.weather = 'None',
  });
  
  factory CalcField.fromJson(Map<String, Object?> json) => _$CalcFieldFromJson(json);
  
  final bool burn;
  final bool crit;
  @JsonKey(name: 'friend_guard')
  final bool friendGuard;
  final bool lightscreen;
  final bool reflect;
  final String terrain;
  final String weather;

  Map<String, Object?> toJson() => _$CalcFieldToJson(this);
}
