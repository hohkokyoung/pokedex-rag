// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'move_row.dart';

part 'move_list_view.g.dart';

@JsonSerializable()
class MoveListView {
  const MoveListView({
    required this.moves,
    this.kind = 'move_list',
    this.chunkRefs,
    this.step,
  });
  
  factory MoveListView.fromJson(Map<String, Object?> json) => _$MoveListViewFromJson(json);
  
  @JsonKey(name: 'chunk_refs')
  final List<int>? chunkRefs;
  final String kind;
  final List<MoveRow> moves;
  final String? step;

  Map<String, Object?> toJson() => _$MoveListViewToJson(this);
}
