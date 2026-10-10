import 'package:flutter/material.dart';

import '../theme/theme.dart';
import '../theme/tokens.g.dart';

/// The website's ground: a faint vertical wash behind every screen (DESIGN.md "Ground").
class Ground extends StatelessWidget {
  const Ground({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) => DecoratedBox(
    decoration: const BoxDecoration(
      gradient: LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: [Color(0xFFF4F2EF), Color(0xFFEAE7F0), Color(0xFFE6ECF2)],
        stops: [0, .55, 1],
      ),
    ),
    child: child,
  );
}

/// A screen's title: Chakra Petch, one per screen.
class PageTitle extends StatelessWidget {
  const PageTitle(this.text, {super.key, this.size = 34});

  final String text;
  final double size;

  @override
  Widget build(BuildContext context) => Text(
    text,
    style: AppText.display.copyWith(fontSize: size, fontWeight: FontWeight.w700, height: 1.05),
  );
}

/// The website's segmented control: an inset track with the chosen segment filled in ink.
/// The indicator slides (200 ms, ease-out-expo); with reduced motion it jumps.
class Segmented<T> extends StatelessWidget {
  const Segmented({super.key, required this.options, required this.value, required this.onChanged, this.compact = false});

  final List<(T value, String label, Key? key)> options;
  final T value;
  final ValueChanged<T> onChanged;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final i = options.indexWhere((o) => o.$1 == value).clamp(0, options.length - 1);
    final still = MediaQuery.of(context).disableAnimations;
    final h = compact ? 32.0 : 38.0;
    return Container(
      height: h + 6,
      padding: const EdgeInsets.all(3),
      decoration: BoxDecoration(color: const Color(0x0E14171D), borderRadius: BorderRadius.circular(Radii.control)),
      child: LayoutBuilder(
        builder: (context, c) {
          final w = c.maxWidth / options.length;
          return Stack(
            children: [
              AnimatedPositioned(
                duration: still ? Duration.zero : const Duration(milliseconds: 200),
                curve: const Cubic(0.16, 1, 0.3, 1),
                left: w * i,
                top: 0,
                width: w,
                height: h,
                child: DecoratedBox(
                  decoration: BoxDecoration(color: Palette.instrumentInk, borderRadius: BorderRadius.circular(Radii.inset)),
                ),
              ),
              Row(
                children: [
                  for (final (k, (v, label, key)) in options.indexed)
                    Expanded(
                      child: Semantics(
                        selected: k == i,
                        button: true,
                        child: InkWell(
                          key: key,
                          borderRadius: BorderRadius.circular(Radii.inset),
                          onTap: () => onChanged(v),
                          child: SizedBox(
                            height: h,
                            child: Center(
                              child: AnimatedDefaultTextStyle(
                                duration: still ? Duration.zero : const Duration(milliseconds: 200),
                                style: AppText.label.copyWith(
                                  fontSize: compact ? 12.5 : 13.5,
                                  color: k == i ? Palette.panelWhite : Palette.mutedSlate,
                                ),
                                child: Text(label, maxLines: 1, overflow: TextOverflow.ellipsis),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                ],
              ),
            ],
          );
        },
      ),
    );
  }
}

/// A label column and a value row whose parts sit 8px apart (a chip never touches text).
class KeyValueRow extends StatelessWidget {
  const KeyValueRow({super.key, required this.label, required this.children, this.first = false});

  final String label;
  final List<Widget> children;
  final bool first;

  @override
  Widget build(BuildContext context) => Container(
    constraints: const BoxConstraints(minHeight: 40),
    decoration: BoxDecoration(
      border: first ? null : const Border(top: BorderSide(color: Palette.hairlineSoft)),
    ),
    padding: const EdgeInsets.symmetric(vertical: 6),
    child: Row(
      children: [
        SizedBox(
          width: 76,
          child: Text(label, style: AppText.bodySmall.copyWith(color: Palette.mutedSlate)),
        ),
        Expanded(
          child: Wrap(spacing: 8, runSpacing: 4, crossAxisAlignment: WrapCrossAlignment.center, children: children),
        ),
      ],
    ),
  );
}

/// A muted note after a value in a [KeyValueRow] ("· Atk ×1.5").
Widget note(String text) => Text(text, style: AppText.bodySmall.copyWith(color: Palette.mutedSlate));

/// The bottom bar: the website's Tray (current tab raised white) plus a separate red Ask.
class TrayBar extends StatelessWidget {
  const TrayBar({super.key, required this.tabs, required this.current, required this.onTap, required this.ask});

  /// (branch index, label, icon, key) for the tray's tabs.
  final List<(int, String, IconData, Key)> tabs;
  final int current;
  final ValueChanged<int> onTap;

  /// (branch index, key) for Ask.
  final (int, Key) ask;

  @override
  Widget build(BuildContext context) {
    final bottom = MediaQuery.of(context).padding.bottom;
    final askOn = current == ask.$1;
    Widget item(String label, IconData icon, bool on, Color fg) => Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(icon, size: 21, color: fg),
        const SizedBox(height: 2),
        Text(label, style: AppText.label.copyWith(fontSize: 11, color: fg)),
      ],
    );
    return Padding(
      padding: EdgeInsets.fromLTRB(Space.gutter, 6, Space.gutter, bottom > 0 ? bottom : 12),
      child: SizedBox(
        height: 58,
        child: Row(
          children: [
            Expanded(
              child: Container(
                padding: const EdgeInsets.all(4),
                decoration: BoxDecoration(
                  color: const Color(0xF0E8EAF0),
                  borderRadius: BorderRadius.circular(Radii.card),
                  border: Border.all(color: Palette.hairline),
                ),
                child: Row(
                  children: [
                    for (final (i, label, icon, key) in tabs)
                      Expanded(
                        child: Semantics(
                          selected: i == current,
                          button: true,
                          label: label,
                          excludeSemantics: true,
                          child: GestureDetector(
                            key: key,
                            behavior: HitTestBehavior.opaque,
                            onTap: () => onTap(i),
                            child: AnimatedContainer(
                              duration: MediaQuery.of(context).disableAnimations ? Duration.zero : const Duration(milliseconds: 200),
                              curve: const Cubic(0.16, 1, 0.3, 1),
                              decoration: BoxDecoration(
                                color: i == current ? Palette.panelWhite : Colors.transparent,
                                borderRadius: BorderRadius.circular(Radii.control),
                                boxShadow: i == current
                                    ? const [BoxShadow(color: Color(0x1414171D), blurRadius: 2, offset: Offset(0, 1))]
                                    : null,
                              ),
                              child: item(label, icon, i == current, i == current ? Palette.instrumentInk : Palette.mutedSlate),
                            ),
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ),
            const SizedBox(width: 8),
            Semantics(
              selected: askOn,
              button: true,
              label: 'Ask',
              excludeSemantics: true,
              child: GestureDetector(
                key: ask.$2,
                onTap: () => onTap(ask.$1),
                child: Container(
                  width: 74,
                  decoration: BoxDecoration(
                    color: Palette.pokeballRed,
                    borderRadius: BorderRadius.circular(Radii.card),
                    border: askOn ? Border.all(color: const Color(0x4DD8310C), width: 3) : null,
                  ),
                  child: item('Ask', askOn ? Icons.chat_bubble : Icons.chat_bubble_outline, askOn, Palette.panelWhite),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// The Dex Lens mark and the pokérag wordmark (masters: frontend/public/brand/, small cut).
class BrandMark extends StatelessWidget {
  const BrandMark({super.key});

  @override
  Widget build(BuildContext context) => Semantics(
    label: 'pokérag',
    excludeSemantics: true,
    child: Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        const SizedBox(width: 24, height: 26, child: CustomPaint(painter: _DexLens())),
        const SizedBox(width: 8),
        Text('pokérag', style: AppText.display.copyWith(fontSize: 22, fontWeight: FontWeight.w700, height: 1)),
      ],
    ),
  );
}

class _DexLens extends CustomPainter {
  const _DexLens();

  @override
  void paint(Canvas canvas, Size size) {
    // The SVG's viewBox is 32..224 × 24..232; draw in its units.
    final s = size.width / 192;
    canvas.scale(s, s);
    canvas.translate(-32, -24);
    final body = Path()
      ..moveTo(32, 48)
      ..arcToPoint(const Offset(56, 24), radius: const Radius.circular(24))
      ..lineTo(161.37, 24)
      ..arcToPoint(const Offset(172.69, 28.69), radius: const Radius.circular(16))
      ..lineTo(219.31, 75.31)
      ..arcToPoint(const Offset(224, 86.63), radius: const Radius.circular(16))
      ..lineTo(224, 208)
      ..arcToPoint(const Offset(200, 232), radius: const Radius.circular(24))
      ..lineTo(56, 232)
      ..arcToPoint(const Offset(32, 208), radius: const Radius.circular(24))
      ..close();
    canvas.drawPath(body, Paint()..color = Palette.brandMarkRed);
    canvas.drawCircle(const Offset(112, 128), 68, Paint()..color = Palette.panelWhite);
    canvas.drawCircle(const Offset(112, 128), 44, Paint()..color = const Color(0xFF2F7BF5));
    canvas.drawCircle(const Offset(96.16, 112.16), 15, Paint()..color = Palette.panelWhite);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

/// A square icon button: white, hairline, 10px corners (the website's icon controls).
class SquareButton extends StatelessWidget {
  const SquareButton({super.key, required this.icon, required this.onPressed, this.tooltip, this.size = 40, this.color});

  final IconData icon;
  final VoidCallback? onPressed;
  final String? tooltip;
  final double size;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final b = Material(
      color: Palette.panelWhite,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(Radii.control),
        side: const BorderSide(color: Palette.hairline),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(Radii.control),
        onTap: onPressed,
        child: SizedBox(
          width: size,
          height: size,
          child: Icon(icon, size: 19, color: color ?? Palette.inkDim),
        ),
      ),
    );
    return tooltip == null ? b : Tooltip(message: tooltip, child: b);
  }
}

/// A screen's top bar: the title in Chakra Petch on the ground (30pt on a tab's first
/// page, 24pt on a page opened from it), left-aligned, with optional actions.
PreferredSizeWidget pageBar(String title, {bool root = false, List<Widget>? actions}) => AppBar(
      toolbarHeight: root ? 64 : 56,
      titleSpacing: root ? Space.gutter : 0,
      title: PageTitle(title, size: root ? 30 : 24),
      actions: [...?actions, if (actions != null) const SizedBox(width: Space.gutter - 4)],
    );

/// The red send button inside a question box (Ask and both coaches): "Ask", or a spinner
/// while an answer streams.
class SendButton extends StatelessWidget {
  const SendButton({super.key, required this.busy, required this.onPressed, this.label = 'Ask'});

  final bool busy;
  final VoidCallback? onPressed;
  final String label;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.all(5),
        child: FilledButton(
          onPressed: busy ? null : onPressed,
          style: FilledButton.styleFrom(
            minimumSize: const Size(64, 40),
            padding: const EdgeInsets.symmetric(horizontal: 14),
            disabledBackgroundColor: Palette.pokeballRed.withValues(alpha: .45),
            disabledForegroundColor: Palette.panelWhite,
          ),
          child: busy
              ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Palette.panelWhite))
              : Text(label, style: AppText.label.copyWith(fontSize: 14, color: Palette.panelWhite)),
        ),
      );
}
