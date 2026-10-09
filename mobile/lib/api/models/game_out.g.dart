// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'game_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

GameOut _$GameOutFromJson(Map<String, dynamic> json) => GameOut(
  generation: (json['generation'] as num).toInt(),
  id: (json['id'] as num).toInt(),
  identifier: json['identifier'] as String,
  learners: (json['learners'] as num).toInt(),
  name: json['name'] as String,
);

Map<String, dynamic> _$GameOutToJson(GameOut instance) => <String, dynamic>{
  'generation': instance.generation,
  'id': instance.id,
  'identifier': instance.identifier,
  'learners': instance.learners,
  'name': instance.name,
};
