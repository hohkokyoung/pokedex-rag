// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'z_user_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ZUserOut _$ZUserOutFromJson(Map<String, dynamic> json) => ZUserOut(
  dexNumber: (json['dex_number'] as num).toInt(),
  id: (json['id'] as num).toInt(),
  name: json['name'] as String,
  spriteUrl: json['sprite_url'] as String,
  formId: (json['form_id'] as num?)?.toInt(),
);

Map<String, dynamic> _$ZUserOutToJson(ZUserOut instance) => <String, dynamic>{
  'dex_number': instance.dexNumber,
  'form_id': instance.formId,
  'id': instance.id,
  'name': instance.name,
  'sprite_url': instance.spriteUrl,
};
