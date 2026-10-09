// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'member_defense.dart';
import 'shared_weakness.dart';

part 'defensive_profile.g.dart';

@JsonSerializable()
class DefensiveProfile {
  const DefensiveProfile({
    required this.matrix,
    required this.sharedWeaknesses,
  });
  
  factory DefensiveProfile.fromJson(Map<String, Object?> json) => _$DefensiveProfileFromJson(json);
  
  final List<MemberDefense> matrix;
  @JsonKey(name: 'shared_weaknesses')
  final List<SharedWeakness> sharedWeaknesses;

  Map<String, Object?> toJson() => _$DefensiveProfileToJson(this);
}
