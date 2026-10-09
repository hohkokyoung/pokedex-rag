// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'learn_group.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

LearnGroup _$LearnGroupFromJson(Map<String, dynamic> json) => LearnGroup(
  label: json['label'] as String,
  method: json['method'] as String,
  moves: (json['moves'] as List<dynamic>)
      .map((e) => LearnMove.fromJson(e as Map<String, dynamic>))
      .toList(),
  ref: (json['ref'] as num?)?.toInt(),
);

Map<String, dynamic> _$LearnGroupToJson(LearnGroup instance) =>
    <String, dynamic>{
      'label': instance.label,
      'method': instance.method,
      'moves': instance.moves,
      'ref': instance.ref,
    };
