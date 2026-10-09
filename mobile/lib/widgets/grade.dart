import 'package:flutter/material.dart';

import '../theme/theme.dart';
import '../theme/tokens.g.dart';

/// Grade colours as on the website: A/B good, C fair, D/F poor.
Color gradeColor(String g) => switch (g) {
      'A' || 'B' => Palette.verdictGreen,
      'C' => Palette.cautionAmber,
      _ => Palette.pokeballRed,
    };

Color gradeTextColor(String g) => switch (g) {
      'A' || 'B' => Palette.verdictGreenText,
      'C' => Palette.cautionAmberText,
      _ => Palette.pokeballRedText,
    };

/// A letter grade in its tone (the letter is always written, colour only adds).
class GradeBadge extends StatelessWidget {
  const GradeBadge(this.grade, {super.key, this.size = 36});

  final String grade;
  final double size;

  @override
  Widget build(BuildContext context) => Container(
        width: size,
        height: size,
        alignment: Alignment.center,
        decoration: BoxDecoration(color: gradeColor(grade), borderRadius: BorderRadius.circular(Radii.inset)),
        child: Text(grade, style: AppText.display.copyWith(fontSize: size * 0.55, color: Palette.panelWhite, height: 1)),
      );
}
