// The generated tokens (lib/theme/tokens.g.dart, from DESIGN.md) cover every type.
import 'package:flutter_test/flutter_test.dart';
import 'package:pokerag/theme/tokens.g.dart';

import 'support/fake_backend.dart';

void main() {
  final types = (fixture('type_chart')! as Map)['order'] as List;

  test('all 18 types have fill, on-fill and text colours', () {
    expect(types, hasLength(18));
    for (final t in types) {
      expect(TypeColors.fill, contains(t), reason: 'fill for $t');
      expect(TypeColors.on, contains(t), reason: 'on for $t');
      expect(TypeColors.text, contains(t), reason: 'text for $t');
    }
  });

  test('brand values match DESIGN.md', () {
    expect(Palette.pokeballRed.toARGB32(), 0xFFD8310C);
    expect(Palette.instrumentInk.toARGB32(), 0xFF14171D);
    expect(Radii.card, 14);
  });
}
