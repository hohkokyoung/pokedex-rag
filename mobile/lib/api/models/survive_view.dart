// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'calc_apply.dart';
import 'calc_ref.dart';
import 'hit_range.dart';
import 'move_row.dart';
import 'survive_view_stat.dart';

part 'survive_view.g.dart';

@JsonSerializable()
class SurviveView {
  const SurviveView({
    required this.attacker,
    required this.current,
    required this.defender,
    required this.hpEv,
    required this.move,
    required this.nature,
    required this.natureChanged,
    required this.range,
    required this.stat,
    required this.statEv,
    required this.survives,
    this.apply,
    this.chunkRefs,
    this.step,
    this.already = false,
    this.kind = 'survive',
  });
  
  factory SurviveView.fromJson(Map<String, Object?> json) => _$SurviveViewFromJson(json);
  
  final bool already;
  final CalcApply? apply;
  final CalcRef attacker;
  @JsonKey(name: 'chunk_refs')
  final List<int>? chunkRefs;
  final HitRange current;
  final CalcRef defender;
  @JsonKey(name: 'hp_ev')
  final int hpEv;
  final String kind;
  final MoveRow move;
  final String nature;
  @JsonKey(name: 'nature_changed')
  final bool natureChanged;
  final HitRange range;
  final SurviveViewStat stat;
  @JsonKey(name: 'stat_ev')
  final int statEv;
  final String? step;
  final bool survives;

  Map<String, Object?> toJson() => _$SurviveViewToJson(this);
}
