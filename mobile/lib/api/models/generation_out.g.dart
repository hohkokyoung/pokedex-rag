// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'generation_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

GenerationOut _$GenerationOutFromJson(Map<String, dynamic> json) =>
    GenerationOut(
      id: (json['id'] as num).toInt(),
      identifier: json['identifier'] as String,
      name: json['name'] as String,
    );

Map<String, dynamic> _$GenerationOutToJson(GenerationOut instance) =>
    <String, dynamic>{
      'id': instance.id,
      'identifier': instance.identifier,
      'name': instance.name,
    };
