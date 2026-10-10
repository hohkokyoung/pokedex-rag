// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'calc_turn_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CalcTurnOut _$CalcTurnOutFromJson(Map<String, dynamic> json) => CalcTurnOut(
  aims: Map<String, int?>.from(json['aims'] as Map),
  hp: (json['hp'] as List<dynamic>)
      .map((e) => CalcHpOut.fromJson(e as Map<String, dynamic>))
      .toList(),
  moves: (json['moves'] as List<dynamic>)
      .map((e) => CalcMoveOut.fromJson(e as Map<String, dynamic>))
      .toList(),
  order: (json['order'] as List<dynamic>)
      .map((e) => CalcOrderOut.fromJson(e as Map<String, dynamic>))
      .toList(),
  steps: (json['steps'] as List<dynamic>)
      .map((e) => CalcStepOut.fromJson(e as Map<String, dynamic>))
      .toList(),
);

Map<String, dynamic> _$CalcTurnOutToJson(CalcTurnOut instance) =>
    <String, dynamic>{
      'aims': instance.aims,
      'hp': instance.hp,
      'moves': instance.moves,
      'order': instance.order,
      'steps': instance.steps,
    };
