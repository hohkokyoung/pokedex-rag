// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'calc_ref.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CalcRef _$CalcRefFromJson(Map<String, dynamic> json) => CalcRef(
  name: json['name'] as String,
  side: (json['side'] as num).toInt(),
  slot: (json['slot'] as num).toInt(),
  dexNumber: (json['dex_number'] as num?)?.toInt(),
);

Map<String, dynamic> _$CalcRefToJson(CalcRef instance) => <String, dynamic>{
  'dex_number': instance.dexNumber,
  'name': instance.name,
  'side': instance.side,
  'slot': instance.slot,
};
