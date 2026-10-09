// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'type_net.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TypeNet _$TypeNetFromJson(Map<String, dynamic> json) =>
    TypeNet(net: (json['net'] as num).toInt(), type: json['type'] as String);

Map<String, dynamic> _$TypeNetToJson(TypeNet instance) => <String, dynamic>{
  'net': instance.net,
  'type': instance.type,
};
