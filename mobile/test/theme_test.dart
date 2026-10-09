// The bundled fonts load from the app's assets, and the theme and type chip use them.
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pokerag/theme/theme.dart';
import 'package:pokerag/theme/tokens.g.dart';
import 'package:pokerag/widgets/type_chip.dart';

Future<void> loadFont(String family, String asset) async {
  final loader = FontLoader(family)..addFont(rootBundle.load(asset));
  await loader.load();
}

void main() {
  setUpAll(() async {
    await loadFont('Chakra Petch', 'assets/fonts/ChakraPetch-SemiBold.ttf');
    await loadFont('Space Grotesk', 'assets/fonts/SpaceGrotesk-Variable.ttf');
    await loadFont('JetBrains Mono', 'assets/fonts/JetBrainsMono-Variable.ttf');
  });

  test('the OFL licences are bundled', () async {
    for (final f in ['ChakraPetch', 'SpaceGrotesk', 'JetBrainsMono']) {
      expect(await rootBundle.loadString('assets/fonts/$f-OFL.txt'), contains('SIL Open Font License'));
    }
  });

  testWidgets('a type chip and a heading render with the bundled families', (tester) async {
    await tester.pumpWidget(MaterialApp(
      theme: AppTheme.light(),
      home: Scaffold(
        body: Column(children: [
          Text('Garchomp', style: AppText.display),
          const TypeChip('dragon'),
        ]),
      ),
    ));
    final heading = tester.widget<Text>(find.text('Garchomp'));
    expect(heading.style!.fontFamily, 'Chakra Petch');
    final chipText = tester.widget<Text>(find.text('Dragon'));
    expect(chipText.style!.fontFamily, 'Space Grotesk');
    expect(chipText.style!.color, TypeColors.on['dragon']);
    final box = tester.widget<Container>(find.ancestor(of: find.text('Dragon'), matching: find.byType(Container)));
    expect((box.decoration! as BoxDecoration).color, TypeColors.fill['dragon']);
  });
}
