// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'coach_ask_request.g.dart';

@JsonSerializable()
class CoachAskRequest {
  const CoachAskRequest({
    required this.question,
    this.opponentId,
  });
  
  factory CoachAskRequest.fromJson(Map<String, Object?> json) => _$CoachAskRequestFromJson(json);
  
  @JsonKey(name: 'opponent_id')
  final int? opponentId;
  final String question;

  Map<String, Object?> toJson() => _$CoachAskRequestToJson(this);
}
