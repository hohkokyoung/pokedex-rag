// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'slot_ability.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SlotAbility _$SlotAbilityFromJson(Map<String, dynamic> json) => SlotAbility(
  id: (json['id'] as num).toInt(),
  name: json['name'] as String,
  isHidden: json['is_hidden'] as bool? ?? false,
);

Map<String, dynamic> _$SlotAbilityToJson(SlotAbility instance) =>
    <String, dynamic>{
      'id': instance.id,
      'is_hidden': instance.isHidden,
      'name': instance.name,
    };
