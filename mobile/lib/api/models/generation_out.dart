// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'generation_out.g.dart';

@JsonSerializable()
class GenerationOut {
  const GenerationOut({
    required this.id,
    required this.identifier,
    required this.name,
  });
  
  factory GenerationOut.fromJson(Map<String, Object?> json) => _$GenerationOutFromJson(json);
  
  final int id;
  final String identifier;
  final String name;

  Map<String, Object?> toJson() => _$GenerationOutToJson(this);
}
