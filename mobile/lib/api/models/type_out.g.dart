// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'type_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TypeOut _$TypeOutFromJson(Map<String, dynamic> json) => TypeOut(
  id: (json['id'] as num).toInt(),
  identifier: json['identifier'] as String,
  name: json['name'] as String,
);

Map<String, dynamic> _$TypeOutToJson(TypeOut instance) => <String, dynamic>{
  'id': instance.id,
  'identifier': instance.identifier,
  'name': instance.name,
};
