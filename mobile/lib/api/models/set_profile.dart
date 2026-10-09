// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'set_member.dart';

part 'set_profile.g.dart';

@JsonSerializable()
class SetProfile {
  const SetProfile({
    required this.members,
  });
  
  factory SetProfile.fromJson(Map<String, Object?> json) => _$SetProfileFromJson(json);
  
  final List<SetMember> members;

  Map<String, Object?> toJson() => _$SetProfileToJson(this);
}
