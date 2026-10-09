// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'favorite_out.g.dart';

@JsonSerializable()
class FavoriteOut {
  const FavoriteOut({
    required this.dexNumber,
    required this.id,
    required this.name,
    required this.spriteUrl,
    required this.types,
  });
  
  factory FavoriteOut.fromJson(Map<String, Object?> json) => _$FavoriteOutFromJson(json);
  
  @JsonKey(name: 'dex_number')
  final int dexNumber;
  final int id;
  final String name;
  @JsonKey(name: 'sprite_url')
  final String spriteUrl;
  final List<String> types;

  Map<String, Object?> toJson() => _$FavoriteOutToJson(this);
}
