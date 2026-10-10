// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'move_game_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MoveGameOut _$MoveGameOutFromJson(Map<String, dynamic> json) => MoveGameOut(
  generation: (json['generation'] as num).toInt(),
  id: (json['id'] as num).toInt(),
  identifier: json['identifier'] as String,
  moveIds: (json['move_ids'] as List<dynamic>)
      .map((e) => (e as num).toInt())
      .toList(),
  name: json['name'] as String,
);

Map<String, dynamic> _$MoveGameOutToJson(MoveGameOut instance) =>
    <String, dynamic>{
      'generation': instance.generation,
      'id': instance.id,
      'identifier': instance.identifier,
      'move_ids': instance.moveIds,
      'name': instance.name,
    };
