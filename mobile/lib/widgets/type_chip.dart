import 'package:flutter/material.dart';

import '../theme/theme.dart';
import '../theme/tokens.g.dart';

/// A type tag: the game-style fill with the type's name, always spelled out (type is
/// never carried by colour alone).
class TypeChip extends StatelessWidget {
  const TypeChip(this.type, {super.key, this.dense = false});

  final String type;
  final bool dense;

  @override
  Widget build(BuildContext context) {
    final label = type.isEmpty ? type : type[0].toUpperCase() + type.substring(1);
    return Container(
      padding: EdgeInsets.symmetric(horizontal: dense ? 7 : 9, vertical: dense ? 2 : 4),
      decoration: BoxDecoration(
        color: TypeColors.fill[type] ?? Palette.mutedSlate,
        borderRadius: BorderRadius.circular(Radii.chip),
      ),
      child: Text(
        label,
        style: AppText.label.copyWith(color: TypeColors.on[type] ?? Palette.panelWhite, fontSize: dense ? 11 : null),
      ),
    );
  }
}
