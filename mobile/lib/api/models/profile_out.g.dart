// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'profile_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ProfileOut _$ProfileOutFromJson(Map<String, dynamic> json) => ProfileOut(
  favorites: (json['favorites'] as List<dynamic>)
      .map((e) => FavoriteOut.fromJson(e as Map<String, dynamic>))
      .toList(),
  preferredTypes: (json['preferred_types'] as List<dynamic>)
      .map((e) => e as String)
      .toList(),
);

Map<String, dynamic> _$ProfileOutToJson(ProfileOut instance) =>
    <String, dynamic>{
      'favorites': instance.favorites,
      'preferred_types': instance.preferredTypes,
    };
