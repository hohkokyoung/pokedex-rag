// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'build_set.dart';
import 'set_edit_view_side.dart';

part 'set_edit_view.g.dart';

/// A proposed set for one member, shown was → now; saved only on Apply.
@JsonSerializable()
class SetEditView {
  const SetEditView({
    required this.after,
    required this.before,
    required this.name,
    required this.side,
    required this.slot,
    required this.teamId,
    this.kind = 'set_edit',
    this.spriteUrl = '',
    this.why = '',
    this.chunkRefs,
    this.fields,
    this.member,
    this.step,
  });
  
  factory SetEditView.fromJson(Map<String, Object?> json) => _$SetEditViewFromJson(json);
  
  final BuildSet after;
  final BuildSet before;
  @JsonKey(name: 'chunk_refs')
  final List<int>? chunkRefs;
  final dynamic fields;
  final String kind;
  final dynamic member;
  final String name;
  final SetEditViewSide side;
  final int slot;
  @JsonKey(name: 'sprite_url')
  final String spriteUrl;
  final String? step;
  @JsonKey(name: 'team_id')
  final int teamId;
  final String why;

  Map<String, Object?> toJson() => _$SetEditViewToJson(this);
}
