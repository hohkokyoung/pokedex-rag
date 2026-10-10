import '../../api/export.dart';

/// A finder row: the generic Z-Moves are stored twice (a physical and a special copy),
/// so same-named moves fold into one row carrying every category (the website's foldMoves).
class FinderMove {
  FinderMove(this.move, this.classes);

  final MoveOut move;
  final List<String> classes;
}

List<FinderMove> foldMoves(List<MoveOut> moves) {
  final byName = <String, FinderMove>{};
  for (final m in moves) {
    final hit = byName[m.name];
    if (hit != null) {
      if (m.damageClass != null && !hit.classes.contains(m.damageClass)) hit.classes.add(m.damageClass!);
    } else {
      byName[m.name] = FinderMove(m, [?m.damageClass]);
    }
  }
  return byName.values.toList();
}

/// Effect text matches at a word start, so "rain" finds Drizzle but not "terrain".
bool Function(String?) effectMatcher(String query) {
  final re = RegExp('\\b${RegExp.escape(query)}', caseSensitive: false);
  return (text) => text != null && re.hasMatch(text);
}

/// Sort by a number; rows without one sink either way, ties by name.
int Function(T, T) byField<T>(num? Function(T) get, String Function(T) name, int dir) => (a, b) {
      final av = get(a), bv = get(b);
      if (av == null || bv == null) {
        return av == null && bv == null ? name(a).compareTo(name(b)) : (av == null ? 1 : -1);
      }
      final c = dir * av.compareTo(bv);
      return c != 0 ? c : name(a).compareTo(name(b));
    };

enum MoveSort { power, pp, accuracy, name }

enum ItemSort { name, cost, fling }

List<FinderMove> filterMoves(
  List<FinderMove> all, {
  String query = '',
  Set<String> types = const {},
  Set<String> categories = const {},
  Set<MoveOutKind> kinds = const {},
  Set<int>? inGame,
  MoveSort sort = MoveSort.power,
  bool ascending = false,
}) {
  final q = query.trim().toLowerCase();
  final out = all
      .where((f) =>
          (q.isEmpty || f.move.name.toLowerCase().contains(q)) &&
          (types.isEmpty || (f.move.type != null && types.contains(f.move.type))) &&
          (categories.isEmpty || f.classes.any(categories.contains)) &&
          (kinds.isEmpty || kinds.contains(f.move.kind)) &&
          // The server's game lists include the Z-Moves and Max Moves of the games that had them.
          (inGame == null || inGame.contains(f.move.id)))
      .toList();
  final dir = ascending ? 1 : -1;
  String name(FinderMove f) => f.move.name;
  out.sort(switch (sort) {
    MoveSort.name => (a, b) => dir * name(a).compareTo(name(b)),
    MoveSort.power => byField((f) => f.move.power, name, dir),
    MoveSort.pp => byField((f) => f.move.pp, name, dir),
    MoveSort.accuracy => byField((f) => f.move.accuracy, name, dir),
  });
  return out;
}

List<AbilityOut> filterAbilities(List<AbilityOut> all, {String query = '', bool ascending = true}) {
  final q = query.trim().toLowerCase();
  final inEffect = effectMatcher(q);
  // Matches the effect text too, so "rain" finds Swift Swim and Drizzle.
  final out = all.where((a) => q.isEmpty || a.name.toLowerCase().contains(q) || inEffect(a.shortEffect ?? a.effect)).toList();
  out.sort((a, b) => (ascending ? 1 : -1) * a.name.compareTo(b.name));
  return out;
}

/// Item categories, most-populated first: (category, count).
List<(String, int)> itemCategories(List<ItemOut> all) {
  final n = <String, int>{};
  for (final i in all) {
    if (i.category != null) n[i.category!] = (n[i.category!] ?? 0) + 1;
  }
  final out = [for (final e in n.entries) (e.key, e.value)];
  out.sort((a, b) => b.$2 != a.$2 ? b.$2.compareTo(a.$2) : a.$1.compareTo(b.$1));
  return out;
}

List<ItemOut> filterItems(
  List<ItemOut> all, {
  String query = '',
  Set<String> categories = const {},
  ItemSort sort = ItemSort.name,
  bool ascending = true,
}) {
  final q = query.trim().toLowerCase();
  final inEffect = effectMatcher(q);
  final out = all
      .where((i) =>
          (q.isEmpty || i.name.toLowerCase().contains(q) || inEffect(i.shortEffect)) &&
          (categories.isEmpty || (i.category != null && categories.contains(i.category))))
      .toList();
  final dir = ascending ? 1 : -1;
  String name(ItemOut i) => i.name;
  // A cost or Fling power of 0 means none: it sinks like a missing one (the website's `|| null`).
  num? nz(int? v) => v == null || v == 0 ? null : v;
  out.sort(switch (sort) {
    ItemSort.name => (a, b) => dir * a.name.compareTo(b.name),
    ItemSort.cost => byField((i) => nz(i.cost), name, dir),
    ItemSort.fling => byField((i) => nz(i.flingPower), name, dir),
  });
  return out;
}
