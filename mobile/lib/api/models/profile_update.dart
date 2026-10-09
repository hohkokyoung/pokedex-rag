// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'profile_update.g.dart';

@JsonSerializable()
class ProfileUpdate {
  const ProfileUpdate({
    required this.preferredTypes,
  });
  
  factory ProfileUpdate.fromJson(Map<String, Object?> json) => _$ProfileUpdateFromJson(json);
  
  @JsonKey(name: 'preferred_types')
  final List<String> preferredTypes;

  Map<String, Object?> toJson() => _$ProfileUpdateToJson(this);
}
