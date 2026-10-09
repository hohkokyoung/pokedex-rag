// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'ask_request.g.dart';

@JsonSerializable()
class AskRequest {
  const AskRequest({
    required this.question,
  });
  
  factory AskRequest.fromJson(Map<String, Object?> json) => _$AskRequestFromJson(json);
  
  final String question;

  Map<String, Object?> toJson() => _$AskRequestToJson(this);
}
