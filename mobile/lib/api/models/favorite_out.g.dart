// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'favorite_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

FavoriteOut _$FavoriteOutFromJson(Map<String, dynamic> json) => FavoriteOut(
  dexNumber: (json['dex_number'] as num).toInt(),
  id: (json['id'] as num).toInt(),
  name: json['name'] as String,
  spriteUrl: json['sprite_url'] as String,
  types: (json['types'] as List<dynamic>).map((e) => e as String).toList(),
);

Map<String, dynamic> _$FavoriteOutToJson(FavoriteOut instance) =>
    <String, dynamic>{
      'dex_number': instance.dexNumber,
      'id': instance.id,
      'name': instance.name,
      'sprite_url': instance.spriteUrl,
      'types': instance.types,
    };
