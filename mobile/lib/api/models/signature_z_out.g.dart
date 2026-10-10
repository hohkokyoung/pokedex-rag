// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'signature_z_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SignatureZOut _$SignatureZOutFromJson(Map<String, dynamic> json) =>
    SignatureZOut(
      baseMove: json['base_move'] as String,
      crystal: json['crystal'] as String,
      users: (json['users'] as List<dynamic>)
          .map((e) => ZUserOut.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$SignatureZOutToJson(SignatureZOut instance) =>
    <String, dynamic>{
      'base_move': instance.baseMove,
      'crystal': instance.crystal,
      'users': instance.users,
    };
