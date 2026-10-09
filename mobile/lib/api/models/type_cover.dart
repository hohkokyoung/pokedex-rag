// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'type_cover.g.dart';

@JsonSerializable()
class TypeCover {
  const TypeCover({
    required this.learnable,
    required this.now,
    required this.type,
  });
  
  factory TypeCover.fromJson(Map<String, Object?> json) => _$TypeCoverFromJson(json);
  
  final bool learnable;
  final bool now;
  final String type;

  Map<String, Object?> toJson() => _$TypeCoverToJson(this);
}
