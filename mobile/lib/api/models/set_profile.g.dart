// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'set_profile.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SetProfile _$SetProfileFromJson(Map<String, dynamic> json) => SetProfile(
  members: (json['members'] as List<dynamic>)
      .map((e) => SetMember.fromJson(e as Map<String, dynamic>))
      .toList(),
);

Map<String, dynamic> _$SetProfileToJson(SetProfile instance) =>
    <String, dynamic>{'members': instance.members};
