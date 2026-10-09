// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'ranking_row.dart';
import 'ranking_view_order.dart';

part 'ranking_view.g.dart';

@JsonSerializable()
class RankingView {
  const RankingView({
    required this.rows,
    required this.stat,
    required this.total,
    this.kind = 'ranking',
    this.order = RankingViewOrder.desc,
    this.chunkRefs,
    this.step,
  });
  
  factory RankingView.fromJson(Map<String, Object?> json) => _$RankingViewFromJson(json);
  
  @JsonKey(name: 'chunk_refs')
  final List<int>? chunkRefs;
  final String kind;
  final RankingViewOrder order;
  final List<RankingRow> rows;
  final String stat;
  final String? step;
  final int total;

  Map<String, Object?> toJson() => _$RankingViewToJson(this);
}
