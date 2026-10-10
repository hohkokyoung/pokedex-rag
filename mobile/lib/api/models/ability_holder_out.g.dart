// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'ability_holder_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

AbilityHolderOut _$AbilityHolderOutFromJson(Map<String, dynamic> json) =>
    AbilityHolderOut(
      dexNumber: (json['dex_number'] as num).toInt(),
      id: (json['id'] as num).toInt(),
      name: json['name'] as String,
      spriteUrl: json['sprite_url'] as String,
      types: (json['types'] as List<dynamic>).map((e) => e as String).toList(),
      isHidden: json['is_hidden'] as bool? ?? false,
    );

Map<String, dynamic> _$AbilityHolderOutToJson(AbilityHolderOut instance) =>
    <String, dynamic>{
      'dex_number': instance.dexNumber,
      'id': instance.id,
      'is_hidden': instance.isHidden,
      'name': instance.name,
      'sprite_url': instance.spriteUrl,
      'types': instance.types,
    };
