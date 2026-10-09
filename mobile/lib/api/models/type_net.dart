// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'type_net.g.dart';

@JsonSerializable()
class TypeNet {
  const TypeNet({
    required this.net,
    required this.type,
  });
  
  factory TypeNet.fromJson(Map<String, Object?> json) => _$TypeNetFromJson(json);
  
  final int net;
  final String type;

  Map<String, Object?> toJson() => _$TypeNetToJson(this);
}
