// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'cream_rule.dart';
import 'sweet_topping.dart';

part 'spin_guide.g.dart';

/// How a spin evolution (Milcery → Alcremie) picks its look; creams in display order.
@JsonSerializable()
class SpinGuide {
  const SpinGuide({
    required this.creams,
    required this.steps,
    required this.toppings,
  });
  
  factory SpinGuide.fromJson(Map<String, Object?> json) => _$SpinGuideFromJson(json);
  
  final List<CreamRule> creams;
  final List<String> steps;
  final List<SweetTopping> toppings;

  Map<String, Object?> toJson() => _$SpinGuideToJson(this);
}
