// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'calc_field.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CalcField _$CalcFieldFromJson(Map<String, dynamic> json) => CalcField(
  burn: json['burn'] as bool? ?? false,
  crit: json['crit'] as bool? ?? false,
  friendGuard: json['friend_guard'] as bool? ?? false,
  lightscreen: json['lightscreen'] as bool? ?? false,
  reflect: json['reflect'] as bool? ?? false,
  terrain: json['terrain'] as String? ?? 'None',
  weather: json['weather'] as String? ?? 'None',
);

Map<String, dynamic> _$CalcFieldToJson(CalcField instance) => <String, dynamic>{
  'burn': instance.burn,
  'crit': instance.crit,
  'friend_guard': instance.friendGuard,
  'lightscreen': instance.lightscreen,
  'reflect': instance.reflect,
  'terrain': instance.terrain,
  'weather': instance.weather,
};
