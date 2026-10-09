// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'favorite_out.dart';

part 'profile_out.g.dart';

@JsonSerializable()
class ProfileOut {
  const ProfileOut({
    required this.favorites,
    required this.preferredTypes,
  });
  
  factory ProfileOut.fromJson(Map<String, Object?> json) => _$ProfileOutFromJson(json);
  
  final List<FavoriteOut> favorites;
  @JsonKey(name: 'preferred_types')
  final List<String> preferredTypes;

  Map<String, Object?> toJson() => _$ProfileOutToJson(this);
}
