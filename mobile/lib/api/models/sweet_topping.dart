// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'sweet_topping.g.dart';

@JsonSerializable()
class SweetTopping {
  const SweetTopping({
    required this.sweet,
    required this.topping,
  });
  
  factory SweetTopping.fromJson(Map<String, Object?> json) => _$SweetToppingFromJson(json);
  
  final String sweet;
  final String topping;

  Map<String, Object?> toJson() => _$SweetToppingToJson(this);
}
