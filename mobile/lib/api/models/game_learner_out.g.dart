// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'game_learner_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

GameLearnerOut _$GameLearnerOutFromJson(Map<String, dynamic> json) =>
    GameLearnerOut(
      dexNumber: (json['dex_number'] as num).toInt(),
      id: (json['id'] as num).toInt(),
      methods: (json['methods'] as List<dynamic>)
          .map((e) => LearnMethodOut.fromJson(e as Map<String, dynamic>))
          .toList(),
      name: json['name'] as String,
      spriteUrl: json['sprite_url'] as String,
      types: (json['types'] as List<dynamic>).map((e) => e as String).toList(),
      formId: (json['form_id'] as num?)?.toInt(),
      also:
          (json['also'] as List<dynamic>?)?.map((e) => e as String).toList() ??
          const [],
    );

Map<String, dynamic> _$GameLearnerOutToJson(GameLearnerOut instance) =>
    <String, dynamic>{
      'also': instance.also,
      'dex_number': instance.dexNumber,
      'form_id': instance.formId,
      'id': instance.id,
      'methods': instance.methods,
      'name': instance.name,
      'sprite_url': instance.spriteUrl,
      'types': instance.types,
    };
