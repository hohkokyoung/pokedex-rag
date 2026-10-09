// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'ranking_view.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

RankingView _$RankingViewFromJson(Map<String, dynamic> json) => RankingView(
  rows: (json['rows'] as List<dynamic>)
      .map((e) => RankingRow.fromJson(e as Map<String, dynamic>))
      .toList(),
  stat: json['stat'] as String,
  total: (json['total'] as num).toInt(),
  kind: json['kind'] as String? ?? 'ranking',
  order: json['order'] == null
      ? RankingViewOrder.desc
      : RankingViewOrder.fromJson(json['order'] as String),
  chunkRefs: (json['chunk_refs'] as List<dynamic>?)
      ?.map((e) => (e as num).toInt())
      .toList(),
  step: json['step'] as String?,
);

Map<String, dynamic> _$RankingViewToJson(RankingView instance) =>
    <String, dynamic>{
      'chunk_refs': instance.chunkRefs,
      'kind': instance.kind,
      'order': _$RankingViewOrderEnumMap[instance.order]!,
      'rows': instance.rows,
      'stat': instance.stat,
      'step': instance.step,
      'total': instance.total,
    };

const _$RankingViewOrderEnumMap = {
  RankingViewOrder.asc: 'asc',
  RankingViewOrder.desc: 'desc',
  RankingViewOrder.$unknown: r'$unknown',
};
