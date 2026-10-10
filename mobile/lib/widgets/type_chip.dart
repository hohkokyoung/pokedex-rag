import 'package:flutter/material.dart';

import '../theme/theme.dart';
import '../theme/tokens.g.dart';

/// A type tag: the game-style fill with the type's name, always spelled out (type is
/// never carried by colour alone).
class TypeChip extends StatelessWidget {
  const TypeChip(this.type, {super.key, this.dense = false, this.count});

  final String type;
  final bool dense;

  /// A count shown inside the chip after the name ("Ground ×2"), lighter.
  final int? count;

  @override
  Widget build(BuildContext context) {
    final label = type.isEmpty ? type : type[0].toUpperCase() + type.substring(1);
    final on = TypeColors.on[type] ?? Palette.panelWhite;
    final style = AppText.label.copyWith(color: on, fontSize: dense ? 11.5 : 12.5, letterSpacing: .2, height: 1.2);
    return Container(
      // Room around the name, so it never reads cramped.
      padding: EdgeInsets.symmetric(horizontal: dense ? 8 : 10, vertical: dense ? 3 : 5),
      decoration: BoxDecoration(
        color: TypeColors.fill[type] ?? Palette.mutedSlate,
        borderRadius: BorderRadius.circular(Radii.chip),
      ),
      child: count != null && count! > 1
          ? Text.rich(
              TextSpan(
                text: label,
                children: [TextSpan(text: '  ×$count', style: style.copyWith(fontWeight: FontWeight.w500, color: on.withValues(alpha: .85)))],
              ),
              style: style,
            )
          : Text(label, style: style),
    );
  }
}
