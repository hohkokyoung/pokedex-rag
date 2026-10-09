// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'spin_guide.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SpinGuide _$SpinGuideFromJson(Map<String, dynamic> json) => SpinGuide(
  creams: (json['creams'] as List<dynamic>)
      .map((e) => CreamRule.fromJson(e as Map<String, dynamic>))
      .toList(),
  steps: (json['steps'] as List<dynamic>).map((e) => e as String).toList(),
  toppings: (json['toppings'] as List<dynamic>)
      .map((e) => SweetTopping.fromJson(e as Map<String, dynamic>))
      .toList(),
);

Map<String, dynamic> _$SpinGuideToJson(SpinGuide instance) => <String, dynamic>{
  'creams': instance.creams,
  'steps': instance.steps,
  'toppings': instance.toppings,
};
