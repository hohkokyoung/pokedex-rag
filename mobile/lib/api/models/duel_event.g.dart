// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'duel_event.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

DuelEvent _$DuelEventFromJson(Map<String, dynamic> json) => DuelEvent(
  kind: json['kind'] as String,
  side: DuelEventSide.fromJson(json['side'] as String),
  turn: (json['turn'] as num).toInt(),
  ability: json['ability'] as String?,
  boosts: (json['boosts'] as Map<String, dynamic>?)?.map(
    (k, e) => MapEntry(k, (e as num).toInt()),
  ),
  hp: json['hp'] as num?,
  item: json['item'] as String?,
  move: json['move'] as String?,
  mult: json['mult'] as num?,
  pct: json['pct'] as num?,
  type: json['type'] as String?,
);

Map<String, dynamic> _$DuelEventToJson(DuelEvent instance) => <String, dynamic>{
  'ability': instance.ability,
  'boosts': instance.boosts,
  'hp': instance.hp,
  'item': instance.item,
  'kind': instance.kind,
  'move': instance.move,
  'mult': instance.mult,
  'pct': instance.pct,
  'side': _$DuelEventSideEnumMap[instance.side]!,
  'turn': instance.turn,
  'type': instance.type,
};

const _$DuelEventSideEnumMap = {
  DuelEventSide.a: 'a',
  DuelEventSide.b: 'b',
  DuelEventSide.$unknown: r'$unknown',
};
