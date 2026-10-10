// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'catch_terms_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CatchTermsOut _$CatchTermsOutFromJson(Map<String, dynamic> json) =>
    CatchTermsOut(
      a: json['a'] as num,
      ball: json['ball'] as num,
      crit: json['crit'] as num,
      hp: (json['hp'] as num).toInt(),
      hpFactor: json['hp_factor'] as num,
      lowLevel: json['low_level'] as num,
      maxHp: (json['max_hp'] as num).toInt(),
      rate: (json['rate'] as num).toInt(),
      shake: json['shake'] as num,
      status: json['status'] as num,
    );

Map<String, dynamic> _$CatchTermsOutToJson(CatchTermsOut instance) =>
    <String, dynamic>{
      'a': instance.a,
      'ball': instance.ball,
      'crit': instance.crit,
      'hp': instance.hp,
      'hp_factor': instance.hpFactor,
      'low_level': instance.lowLevel,
      'max_hp': instance.maxHp,
      'rate': instance.rate,
      'shake': instance.shake,
      'status': instance.status,
    };
