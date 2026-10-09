// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'form_ability_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

FormAbilityOut _$FormAbilityOutFromJson(Map<String, dynamic> json) =>
    FormAbilityOut(
      identifier: json['identifier'] as String,
      name: json['name'] as String,
      isHidden: json['is_hidden'] as bool? ?? false,
      effect: json['effect'] as String?,
      id: (json['id'] as num?)?.toInt(),
    );

Map<String, dynamic> _$FormAbilityOutToJson(FormAbilityOut instance) =>
    <String, dynamic>{
      'effect': instance.effect,
      'id': instance.id,
      'identifier': instance.identifier,
      'is_hidden': instance.isHidden,
      'name': instance.name,
    };
