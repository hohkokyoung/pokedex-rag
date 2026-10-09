// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'duel_out.dart';

part 'duel_view.g.dart';

/// One pairing played out turn by turn by the deterministic duel engine.
@JsonSerializable()
class DuelView {
  const DuelView({
    required this.duel,
    required this.opponentId,
    required this.teamId,
    this.kind = 'duel',
    this.chunkRefs,
    this.step,
  });
  
  factory DuelView.fromJson(Map<String, Object?> json) => _$DuelViewFromJson(json);
  
  @JsonKey(name: 'chunk_refs')
  final List<int>? chunkRefs;
  final DuelOut duel;
  final String kind;
  @JsonKey(name: 'opponent_id')
  final int opponentId;
  final String? step;
  @JsonKey(name: 'team_id')
  final int teamId;

  Map<String, Object?> toJson() => _$DuelViewToJson(this);
}
