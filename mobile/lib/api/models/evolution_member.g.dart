// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'evolution_member.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

EvolutionMember _$EvolutionMemberFromJson(Map<String, dynamic> json) =>
    EvolutionMember(
      dexNumber: (json['dex_number'] as num).toInt(),
      id: (json['id'] as num).toInt(),
      name: json['name'] as String,
      spriteUrl: json['sprite_url'] as String,
      types: (json['types'] as List<dynamic>).map((e) => e as String).toList(),
      variants:
          (json['variants'] as List<dynamic>?)
              ?.map(
                (e) => CosmeticVariantOut.fromJson(e as Map<String, dynamic>),
              )
              .toList() ??
          const [],
      formId: (json['form_id'] as num?)?.toInt(),
    );

Map<String, dynamic> _$EvolutionMemberToJson(EvolutionMember instance) =>
    <String, dynamic>{
      'dex_number': instance.dexNumber,
      'form_id': instance.formId,
      'id': instance.id,
      'name': instance.name,
      'sprite_url': instance.spriteUrl,
      'types': instance.types,
      'variants': instance.variants,
    };
