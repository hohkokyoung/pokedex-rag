// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'catch_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CatchOut _$CatchOutFromJson(Map<String, dynamic> json) => CatchOut(
  balls: (json['balls'] as List<dynamic>)
      .map((e) => BallOddsOut.fromJson(e as Map<String, dynamic>))
      .toList(),
  captureRate: (json['capture_rate'] as num).toInt(),
  name: json['name'] as String,
  pokemonId: (json['pokemon_id'] as num).toInt(),
);

Map<String, dynamic> _$CatchOutToJson(CatchOut instance) => <String, dynamic>{
  'balls': instance.balls,
  'capture_rate': instance.captureRate,
  'name': instance.name,
  'pokemon_id': instance.pokemonId,
};
