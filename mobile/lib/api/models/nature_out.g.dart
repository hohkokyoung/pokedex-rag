// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'nature_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

NatureOut _$NatureOutFromJson(Map<String, dynamic> json) => NatureOut(
  id: (json['id'] as num).toInt(),
  identifier: json['identifier'] as String,
  name: json['name'] as String,
  decreasedStat: json['decreased_stat'] as String?,
  increasedStat: json['increased_stat'] as String?,
);

Map<String, dynamic> _$NatureOutToJson(NatureOut instance) => <String, dynamic>{
  'decreased_stat': instance.decreasedStat,
  'id': instance.id,
  'identifier': instance.identifier,
  'increased_stat': instance.increasedStat,
  'name': instance.name,
};
