// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'opponent_threat.g.dart';

@JsonSerializable()
class OpponentThreat {
  const OpponentThreat({
    required this.opponentName,
    required this.opponentTypes,
    required this.threatens,
    required this.via,
  });
  
  factory OpponentThreat.fromJson(Map<String, Object?> json) => _$OpponentThreatFromJson(json);
  
  @JsonKey(name: 'opponent_name')
  final String opponentName;
  @JsonKey(name: 'opponent_types')
  final List<String> opponentTypes;
  final List<String> threatens;
  final List<String> via;

  Map<String, Object?> toJson() => _$OpponentThreatToJson(this);
}
