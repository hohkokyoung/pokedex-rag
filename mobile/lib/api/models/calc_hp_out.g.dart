// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'calc_hp_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CalcHpOut _$CalcHpOutFromJson(Map<String, dynamic> json) => CalcHpOut(
  hi: json['hi'] as num,
  lo: json['lo'] as num,
  sash: json['sash'] as bool,
  slot: (json['slot'] as num).toInt(),
);

Map<String, dynamic> _$CalcHpOutToJson(CalcHpOut instance) => <String, dynamic>{
  'hi': instance.hi,
  'lo': instance.lo,
  'sash': instance.sash,
  'slot': instance.slot,
};
