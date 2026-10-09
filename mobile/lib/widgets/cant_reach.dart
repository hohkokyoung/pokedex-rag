import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../theme/theme.dart';
import '../theme/tokens.g.dart';

/// Shown instead of content when the server doesn't answer, never an empty list.
class CantReach extends StatelessWidget {
  const CantReach({super.key, required this.address, required this.onRetry});

  final String address;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(Space.gutter * 2),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text("Can't reach the server", style: AppText.headline),
            const SizedBox(height: Space.sm),
            Text('Nothing answered at', style: AppText.body.copyWith(color: Palette.inkDim)),
            const SizedBox(height: Space.xs),
            Text(address, style: AppText.readout),
            const SizedBox(height: Space.sm),
            Text(
              'Check that pokérag is running on your Mac and that this phone is on the same Wi-Fi.',
              style: AppText.bodySmall.copyWith(color: Palette.mutedSlate),
            ),
            const SizedBox(height: Space.lg),
            // Wraps on narrow screens rather than overflowing.
            Wrap(spacing: Space.sm, runSpacing: Space.sm, children: [
              FilledButton(key: const Key('retry'), onPressed: onRetry, child: const Text('Retry')),
              OutlinedButton(
                key: const Key('change-address'),
                onPressed: () => context.push('/settings'),
                child: const Text('Change address'),
              ),
            ]),
          ],
        ),
      ),
    );
  }
}
