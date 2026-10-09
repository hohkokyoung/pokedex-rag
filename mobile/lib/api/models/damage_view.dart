// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'calc_apply.dart';
import 'calc_ref.dart';
import 'hit_range.dart';
import 'move_row.dart';

part 'damage_view.g.dart';

@JsonSerializable()
class DamageView {
  const DamageView({
    required this.attacker,
    required this.current,
    required this.defender,
    required this.move,
    this.kind = 'damage',
    this.apply,
    this.changes,
    this.chunkRefs,
    this.step,
    this.whatif,
  });
  
  factory DamageView.fromJson(Map<String, Object?> json) => _$DamageViewFromJson(json);
  
  final List<CalcApply>? apply;
  final CalcRef attacker;
  final List<dynamic>? changes;
  @JsonKey(name: 'chunk_refs')
  final List<int>? chunkRefs;
  final HitRange current;
  final CalcRef defender;
  final String kind;
  final MoveRow move;
  final String? step;
  final HitRange? whatif;

  Map<String, Object?> toJson() => _$DamageViewToJson(this);
}
