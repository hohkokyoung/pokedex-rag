// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'calc_option_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CalcOptionOut _$CalcOptionOutFromJson(Map<String, dynamic> json) =>
    CalcOptionOut(
      name: json['name'] as String,
      note: json['note'] as String,
      side: CalcOptionOutSide.fromJson(json['side'] as String),
    );

Map<String, dynamic> _$CalcOptionOutToJson(CalcOptionOut instance) =>
    <String, dynamic>{
      'name': instance.name,
      'note': instance.note,
      'side': _$CalcOptionOutSideEnumMap[instance.side]!,
    };

const _$CalcOptionOutSideEnumMap = {
  CalcOptionOutSide.a: 'a',
  CalcOptionOutSide.d: 'd',
  CalcOptionOutSide.$unknown: r'$unknown',
};
