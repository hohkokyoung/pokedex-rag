// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'z_user_out.g.dart';

@JsonSerializable()
class ZUserOut {
  const ZUserOut({
    required this.dexNumber,
    required this.id,
    required this.name,
    required this.spriteUrl,
    this.formId,
  });
  
  factory ZUserOut.fromJson(Map<String, Object?> json) => _$ZUserOutFromJson(json);
  
  @JsonKey(name: 'dex_number')
  final int dexNumber;
  @JsonKey(name: 'form_id')
  final int? formId;
  final int id;
  final String name;
  @JsonKey(name: 'sprite_url')
  final String spriteUrl;

  Map<String, Object?> toJson() => _$ZUserOutToJson(this);
}
