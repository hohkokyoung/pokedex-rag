// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'type_out.g.dart';

@JsonSerializable()
class TypeOut {
  const TypeOut({
    required this.id,
    required this.identifier,
    required this.name,
  });
  
  factory TypeOut.fromJson(Map<String, Object?> json) => _$TypeOutFromJson(json);
  
  final int id;
  final String identifier;
  final String name;

  Map<String, Object?> toJson() => _$TypeOutToJson(this);
}
