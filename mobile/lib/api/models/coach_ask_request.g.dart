// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'coach_ask_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CoachAskRequest _$CoachAskRequestFromJson(Map<String, dynamic> json) =>
    CoachAskRequest(
      question: json['question'] as String,
      opponentId: (json['opponent_id'] as num?)?.toInt(),
    );

Map<String, dynamic> _$CoachAskRequestToJson(CoachAskRequest instance) =>
    <String, dynamic>{
      'opponent_id': instance.opponentId,
      'question': instance.question,
    };
