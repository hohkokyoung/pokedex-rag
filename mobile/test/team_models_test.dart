// Team responses recorded from the running backend decode into the generated models.
import 'package:flutter_test/flutter_test.dart';
import 'package:pokerag/api/export.dart';

import 'support/fake_backend.dart';

Map<String, Object?> j(String n) => fixture(n)! as Map<String, Object?>;

void main() {
  test('teams, analysis (with and without opponent), strategy and summary decode', () {
    final list = TeamListResponse.fromJson(j('teams'));
    expect(list.teams.map((t) => t.name), contains('Garchomp team'));
    final team = TeamOut.fromJson(j('team_456'));
    expect(team.members, hasLength(6));
    final a = TeamAnalysis.fromJson(j('analysis_456'));
    expect(a.rating!.overall, 88);
    expect(a.rating!.grade, TeamRatingGrade.a);
    final vs = TeamAnalysis.fromJson(j('analysis_456_vs_554'));
    expect(vs.rating, isNull);
    expect(vs.vsOpponent!.verdict!.label, 'Even');
    expect(TeamStrategy.fromJson(j('strategy_456')).style, 'Hyper offense');
    expect(TeamSummaryOut.fromJson(j('summary_456')).text, isNotEmpty);
  });

  test('builder lookups decode', () {
    final abilities = (fixture('abilities_445')! as List).map((e) => AbilityOut.fromJson(e as Map<String, Object?>));
    expect(abilities.any((x) => x.name == 'Rough Skin' && x.isHidden), isTrue);
    final items = (fixture('items_scarf')! as List).map((e) => ItemOut.fromJson(e as Map<String, Object?>));
    expect(items.map((i) => i.name), contains('Choice Scarf'));
    final natures = (fixture('natures')! as List).map((e) => NatureOut.fromJson(e as Map<String, Object?>));
    expect(natures.firstWhere((n) => n.name == 'Jolly').increasedStat, 'speed');
    final moves = (fixture('learnset_445')! as List).map((e) => LearnsetMoveOut.fromJson(e as Map<String, Object?>));
    expect(moves.map((m) => m.name), containsAll(['Earthquake', 'Outrage', 'Stone Edge', 'Fire Fang']));
  });
}
