// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'strategy_contributor.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

StrategyContributor _$StrategyContributorFromJson(Map<String, dynamic> json) =>
    StrategyContributor(
      moves: (json['moves'] as List<dynamic>).map((e) => e as String).toList(),
      name: json['name'] as String,
      setValue: json['set'] as bool,
    );

Map<String, dynamic> _$StrategyContributorToJson(
  StrategyContributor instance,
) => <String, dynamic>{
  'moves': instance.moves,
  'name': instance.name,
  'set': instance.setValue,
};
