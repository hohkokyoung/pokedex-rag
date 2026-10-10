import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

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
  const PageTitle(this.text, {super.key, this.size = 30});

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

/// The bottom bar: one white capsule of equal tabs. The current tab sits on a soft ink
/// capsule that slides between them; Ask is the one red tab (the app's main action).
class NavBar extends StatelessWidget {
  const NavBar({super.key, required this.tabs, required this.current, required this.onTap});

  /// (branch index, label, icon, selected icon, key, red) in display order.
  final List<(int, String, IconData, IconData, Key, bool)> tabs;
  final int current;
  final ValueChanged<int> onTap;

  @override
  Widget build(BuildContext context) {
    final bottom = MediaQuery.of(context).padding.bottom;
    final still = MediaQuery.of(context).disableAnimations;
    final at = tabs.indexWhere((t) => t.$1 == current);
    final red = at >= 0 && tabs[at].$6;
    return Padding(
      padding: EdgeInsets.fromLTRB(Space.gutter, 6, Space.gutter, bottom > 0 ? bottom - 6 : 12),
      child: Container(
        height: 60,
        padding: const EdgeInsets.all(5),
        decoration: BoxDecoration(
          color: Palette.panelWhite,
          borderRadius: BorderRadius.circular(Radii.card + 4),
          border: Border.all(color: Palette.hairline),
        ),
        child: LayoutBuilder(
          builder: (context, c) {
            final w = c.maxWidth / tabs.length;
            return Stack(
              children: [
                if (at >= 0)
                  AnimatedPositioned(
                    duration: still ? Duration.zero : const Duration(milliseconds: 260),
                    curve: const Cubic(0.16, 1, 0.3, 1),
                    left: w * at,
                    top: 0,
                    bottom: 0,
                    width: w,
                    child: DecoratedBox(
                      decoration: BoxDecoration(
                        color: red ? const Color(0x14D8310C) : const Color(0x0F14171D),
                        borderRadius: BorderRadius.circular(Radii.card),
                      ),
                    ),
                  ),
                Row(
                  children: [
                    for (final (i, label, icon, onIcon, key, isRed) in tabs)
                      Expanded(
                        child: _NavItem(
                          key: key,
                          label: label,
                          icon: i == current ? onIcon : icon,
                          on: i == current,
                          red: isRed,
                          onTap: () {
                            if (i != current) HapticFeedback.selectionClick();
                            onTap(i);
                          },
                        ),
                      ),
                  ],
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _NavItem extends StatelessWidget {
  const _NavItem({super.key, required this.label, required this.icon, required this.on, required this.red, required this.onTap});

  final String label;
  final IconData icon;
  final bool on;
  final bool red;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final fg = red ? Palette.pokeballRed : (on ? Palette.instrumentInk : Palette.mutedSlate);
    return Semantics(
      selected: on,
      button: true,
      label: label,
      excludeSemantics: true,
      child: Pressable(
        onTap: onTap,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 22, color: fg),
            const SizedBox(height: 2),
            Text(
              label,
              style: AppText.label.copyWith(fontSize: 10.5, color: fg, fontWeight: on ? FontWeight.w600 : FontWeight.w500),
            ),
          ],
        ),
      ),
    );
  }
}

/// iOS-style press feedback: the child dims and settles slightly while held, with no
/// ripple. The whole box is the tap target.
class Pressable extends StatefulWidget {
  const Pressable({super.key, required this.child, required this.onTap});

  final Widget child;
  final VoidCallback? onTap;

  @override
  State<Pressable> createState() => _PressableState();
}

class _PressableState extends State<Pressable> {
  var _down = false;

  void _set(bool v) {
    if (_down != v) setState(() => _down = v);
  }

  @override
  Widget build(BuildContext context) {
    final still = MediaQuery.of(context).disableAnimations;
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTapDown: widget.onTap == null ? null : (_) => _set(true),
      onTapUp: (_) => _set(false),
      onTapCancel: () => _set(false),
      onTap: widget.onTap,
      child: AnimatedOpacity(
        duration: still ? Duration.zero : Duration(milliseconds: _down ? 60 : 180),
        opacity: _down ? .55 : 1,
        child: AnimatedScale(
          duration: still ? Duration.zero : Duration(milliseconds: _down ? 60 : 180),
          scale: _down ? .96 : 1,
          child: widget.child,
        ),
      ),
    );
  }
}

/// The app's activity indicator (iOS style, not Material's ring).
class Spinner extends StatelessWidget {
  const Spinner({super.key, this.radius = 11, this.color});

  final double radius;
  final Color? color;

  @override
  Widget build(BuildContext context) => CupertinoActivityIndicator(radius: radius, color: color);
}

/// A row in a choice sheet: label (and a note), a red check when chosen.
class ChoiceRow extends StatelessWidget {
  const ChoiceRow({super.key, required this.label, this.hint, required this.selected, required this.onTap});

  final String label;
  final String? hint;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Semantics(
    selected: selected,
    button: true,
    child: InkWell(
      onTap: onTap,
      child: Container(
        constraints: const BoxConstraints(minHeight: 50),
        padding: const EdgeInsets.symmetric(horizontal: Space.gutter, vertical: 10),
        decoration: const BoxDecoration(border: Border(bottom: BorderSide(color: Palette.hairlineSoft))),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(label, style: AppText.body.copyWith(fontWeight: selected ? FontWeight.w600 : FontWeight.w400)),
                  if (hint != null) Text(hint!, style: AppText.bodySmall.copyWith(color: Palette.mutedSlate)),
                ],
              ),
            ),
            const SizedBox(width: Space.sm),
            SizedBox(width: 22, child: selected ? const Icon(Icons.check, size: 20, color: Palette.pokeballRed) : null),
          ],
        ),
      ),
    ),
  );
}

/// A sheet of choices with checks. With [many], rows toggle and the sheet stays open
/// ([onChanged] gets the whole set each time); otherwise picking a row closes it. Long
/// lists (moves, items, natures…) get a search box that matches the label and its note.
Future<void> showChoices<T>(
  BuildContext context, {
  required String title,
  required List<(T, String, String?)> options,
  required Set<T> selected,
  required ValueChanged<Set<T>> onChanged,
  bool many = false,
  String Function(String label)? keyOf,
}) => showModalBottomSheet<void>(
  context: context,
  useRootNavigator: true,
  showDragHandle: true,
  isScrollControlled: true,
  builder: (sheet) {
    var picked = {...selected};
    var q = '';
    final searchable = options.length > 12;
    return StatefulBuilder(
      builder: (context, setSheet) {
        final needle = q.trim().toLowerCase();
        final shown = needle.isEmpty
            ? options
            : [
                for (final o in options)
                  if (o.$2.toLowerCase().contains(needle) || (o.$3?.toLowerCase().contains(needle) ?? false)) o,
              ];
        return Padding(
          // Above the keyboard while searching.
          padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
          child: ConstrainedBox(
            constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * (searchable ? .85 : .75)),
            child: SafeArea(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Padding(
                    padding: const EdgeInsets.fromLTRB(Space.gutter, 0, Space.gutter, Space.xs),
                    child: Text(title, style: AppText.headline),
                  ),
                  if (searchable)
                    Padding(
                      padding: const EdgeInsets.fromLTRB(Space.gutter, 4, Space.gutter, Space.xs),
                      child: TextField(
                        key: const Key('choices-search'),
                        autocorrect: false,
                        onChanged: (v) => setSheet(() => q = v),
                        decoration: InputDecoration(
                          isDense: true,
                          prefixIcon: const Icon(Icons.search, size: 18, color: Palette.mutedSlate),
                          hintText: 'Search ${title.toLowerCase()}',
                        ),
                      ),
                    ),
                  Flexible(
                    child: shown.isEmpty
                        ? Padding(
                            padding: const EdgeInsets.all(Space.gutter),
                            child: Text('Nothing matches.', style: AppText.body.copyWith(color: Palette.mutedSlate)),
                          )
                        : ListView(
                            shrinkWrap: true,
                            keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
                            children: [
                              for (final (v, label, hint) in shown)
                                ChoiceRow(
                                  key: Key(keyOf?.call(label) ?? 'pick-$label'),
                                  label: label,
                                  hint: hint,
                                  selected: picked.contains(v),
                                  onTap: () {
                                    HapticFeedback.selectionClick();
                                    if (many) {
                                      setSheet(() => picked = picked.contains(v) ? ({...picked}..remove(v)) : {...picked, v});
                                      onChanged(picked);
                                    } else {
                                      onChanged({v});
                                      Navigator.of(sheet).pop();
                                    }
                                  },
                                ),
                            ],
                          ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  },
);

/// A one-of-many control (the app's dropdown): the current choice and a chevron; tapping
/// opens a check sheet. Replaces Material's dropdown menu.
class PickerButton<T> extends StatelessWidget {
  const PickerButton({
    super.key,
    required this.title,
    required this.value,
    required this.options,
    required this.onChanged,
    this.placeholder,
    this.expand = true,
    this.style,
  });

  final String title;
  final T value;

  /// (value, label, note).
  final List<(T, String, String?)> options;
  final ValueChanged<T> onChanged;
  final String? placeholder;
  final bool expand;
  final TextStyle? style;

  @override
  Widget build(BuildContext context) {
    final hit = options.where((o) => o.$1 == value).firstOrNull;
    final text = hit == null ? (placeholder ?? title) : (hit.$3 == null ? hit.$2 : '${hit.$2} · ${hit.$3}');
    final label = Text(
      text,
      maxLines: 1,
      overflow: TextOverflow.ellipsis,
      style: (style ?? AppText.body).copyWith(color: hit == null ? Palette.mutedSlate : Palette.instrumentInk),
    );
    return Material(
      color: Palette.panelWhite,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(Radii.control),
        side: const BorderSide(color: Palette.hairline),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(Radii.control),
        onTap: () => showChoices<T>(
          context,
          title: title,
          options: options,
          selected: {if (hit != null) value},
          onChanged: (s) => onChanged(s.first),
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          child: Row(
            mainAxisSize: expand ? MainAxisSize.max : MainAxisSize.min,
            children: [
              if (expand) Expanded(child: label) else Flexible(child: label),
              const SizedBox(width: 6),
              const Icon(Icons.unfold_more, size: 18, color: Palette.mutedSlate),
            ],
          ),
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
      title: PageTitle(title, size: root ? 28 : 22),
      actions: [...?actions, if (actions != null) const SizedBox(width: Space.gutter - 4)],
    );

/// The send button inside a question box (Ask and both coaches): a small red circle
/// with an up arrow, as in iOS Messages; a spinner while an answer streams. [label] is
/// what it says to screen readers.
class SendButton extends StatelessWidget {
  const SendButton({super.key, required this.busy, required this.onPressed, this.label = 'Ask'});

  final bool busy;
  final VoidCallback? onPressed;
  final String label;

  @override
  Widget build(BuildContext context) => Semantics(
    button: true,
    label: label,
    excludeSemantics: true,
    child: Padding(
      // A clear gap from the text before it.
      padding: const EdgeInsets.fromLTRB(14, 6, 7, 6),
      child: Pressable(
        onTap: busy ? null : onPressed,
        child: AnimatedContainer(
          duration: MediaQuery.of(context).disableAnimations ? Duration.zero : const Duration(milliseconds: 160),
          width: 34,
          height: 34,
          decoration: BoxDecoration(
            color: busy ? Palette.pokeballRed.withValues(alpha: .5) : Palette.pokeballRed,
            borderRadius: BorderRadius.circular(Radii.control),
          ),
          child: Center(
            child: busy
                ? const Spinner(radius: 7, color: Palette.panelWhite)
                : const Icon(Icons.arrow_upward_rounded, size: 20, color: Palette.panelWhite),
          ),
        ),
      ),
    ),
  );
}

/// A filter control: white and hairline when off, ink-filled when it holds a choice; a
/// tap opens that filter's sheet.
class FilterPill extends StatelessWidget {
  const FilterPill({super.key, required this.label, required this.on, required this.onTap, this.icon = Icons.expand_more});

  final String label;
  final bool on;
  final VoidCallback onTap;
  final IconData icon;

  @override
  Widget build(BuildContext context) => Semantics(
    button: true,
    selected: on,
    child: Pressable(
      onTap: onTap,
      child: Container(
        height: 34,
        padding: const EdgeInsets.only(left: 12, right: 8),
        decoration: BoxDecoration(
          color: on ? Palette.instrumentInk : Palette.panelWhite,
          borderRadius: BorderRadius.circular(Radii.control),
          border: Border.all(color: on ? Palette.instrumentInk : Palette.hairline),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 180),
              child: Text(
                label,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: AppText.label.copyWith(fontSize: 13, color: on ? Palette.panelWhite : Palette.inkDim),
              ),
            ),
            const SizedBox(width: 2),
            Icon(icon, size: 16, color: on ? Palette.panelWhite : Palette.mutedSlate),
          ],
        ),
      ),
    ),
  );
}

/// A sheet with a title and free content (a type grid, a sort list), sized to it.
Future<void> showPanelSheet(BuildContext context, {required String title, required WidgetBuilder builder}) =>
    showModalBottomSheet<void>(
      context: context,
      useRootNavigator: true,
      showDragHandle: true,
      isScrollControlled: true,
      builder: (context) => ConstrainedBox(
        constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * .8),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(Space.gutter, 0, Space.gutter, Space.md),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(title, style: AppText.headline),
                const SizedBox(height: Space.sm),
                builder(context),
              ],
            ),
          ),
        ),
      ),
    );

/// A white panel whose header (title, a muted summary, a chevron) folds its body open
/// and shut. The body stays out of the tree while shut.
class FoldPanel extends StatefulWidget {
  const FoldPanel({super.key, required this.title, required this.child, this.summary, this.open = false});

  final String title;
  final String? summary;
  final Widget child;
  final bool open;

  @override
  State<FoldPanel> createState() => _FoldPanelState();
}

class _FoldPanelState extends State<FoldPanel> {
  late var _open = widget.open;

  @override
  Widget build(BuildContext context) {
    final still = MediaQuery.of(context).disableAnimations;
    const curve = Cubic(0.16, 1, 0.3, 1);
    return Card(
      child: AnimatedSize(
        duration: still ? Duration.zero : const Duration(milliseconds: 260),
        curve: curve,
        alignment: Alignment.topCenter,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Semantics(
              button: true,
              expanded: _open,
              child: Pressable(
                onTap: () => setState(() => _open = !_open),
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(Space.md, 14, Space.sm + 4, 14),
                  child: Row(
                    children: [
                      Text(widget.title, style: AppText.title),
                      if (widget.summary != null) ...[
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            widget.summary!,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: AppText.bodySmall.copyWith(color: Palette.mutedSlate),
                          ),
                        ),
                      ] else
                        const Spacer(),
                      AnimatedRotation(
                        turns: _open ? .5 : 0,
                        duration: still ? Duration.zero : const Duration(milliseconds: 260),
                        curve: curve,
                        child: const Icon(Icons.expand_more, size: 20, color: Palette.mutedSlate),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            if (_open)
              Padding(padding: const EdgeInsets.fromLTRB(Space.md, 0, Space.md, Space.md), child: widget.child),
          ],
        ),
      ),
    );
  }
}

/// A settings row with an iOS switch: the label (and a note) on the left.
class SwitchRow extends StatelessWidget {
  const SwitchRow({super.key, required this.label, required this.value, required this.onChanged, this.note, this.first = false});

  final String label;
  final String? note;
  final bool value;
  final ValueChanged<bool> onChanged;
  final bool first;

  @override
  Widget build(BuildContext context) => Container(
    constraints: const BoxConstraints(minHeight: 46),
    decoration: BoxDecoration(border: first ? null : const Border(top: BorderSide(color: Palette.hairlineSoft))),
    child: Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(label, style: AppText.body),
              if (note != null) Text(note!, style: AppText.bodySmall.copyWith(color: Palette.mutedSlate)),
            ],
          ),
        ),
        CupertinoSwitch(value: value, onChanged: onChanged, activeTrackColor: Palette.instrumentInk),
      ],
    ),
  );
}

/// A labelled slider: the label and its value on one line, the track full width below.
class LabeledSlider extends StatelessWidget {
  const LabeledSlider({
    super.key,
    required this.label,
    required this.value,
    required this.v,
    required this.min,
    required this.max,
    required this.onChanged,
    this.onEnd,
    this.sliderKey,
  });

  final String label;
  final String value;
  final double v;
  final double min;
  final double max;
  final ValueChanged<double> onChanged;
  final ValueChanged<double>? onEnd;
  final Key? sliderKey;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      Padding(
        padding: const EdgeInsets.only(top: 6),
        child: Row(
          children: [
            Expanded(child: Text(label, style: AppText.bodySmall.copyWith(color: Palette.inkDim))),
            Text(value, style: AppText.readout.copyWith(fontSize: 12, color: Palette.instrumentInk)),
          ],
        ),
      ),
      SliderTheme(
        // Flush with the label above: no Material side padding.
        data: SliderTheme.of(context).copyWith(padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 4)),
        child: Slider(
          key: sliderKey,
          value: v.clamp(min, max),
          min: min,
          max: max,
          divisions: (max - min).round(),
          onChanged: onChanged,
          onChangeEnd: onEnd,
        ),
      ),
    ],
  );
}

/// A one-of-many choice as a settings row (iOS style): the label on the left, the
/// current value on the right in grey with a chevron; a tap opens the check sheet.
class PickerRow<T> extends StatelessWidget {
  const PickerRow({
    super.key,
    required this.label,
    required this.value,
    required this.options,
    required this.onChanged,
    this.placeholder,
    this.first = false,
    this.keyOf,
  });

  final String label;
  final T value;

  /// (value, label, note).
  final List<(T, String, String?)> options;
  final ValueChanged<T> onChanged;
  final String? placeholder;
  final bool first;
  final String Function(String label)? keyOf;

  @override
  Widget build(BuildContext context) {
    final hit = options.where((o) => o.$1 == value).firstOrNull;
    return Semantics(
      button: true,
      label: '$label: ${hit?.$2 ?? placeholder ?? 'none'}',
      excludeSemantics: true,
      child: Pressable(
        onTap: () => showChoices<T>(
          context,
          title: label,
          options: options,
          selected: {if (hit != null) value},
          onChanged: (s) => onChanged(s.first),
          keyOf: keyOf,
        ),
        child: Container(
          constraints: const BoxConstraints(minHeight: 46),
          decoration: BoxDecoration(border: first ? null : const Border(top: BorderSide(color: Palette.hairlineSoft))),
          child: Row(
            children: [
              Text(label, style: AppText.body),
              const SizedBox(width: Space.md),
              Expanded(
                child: Text(
                  hit?.$2 ?? placeholder ?? 'None',
                  textAlign: TextAlign.right,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: AppText.body.copyWith(color: Palette.mutedSlate),
                ),
              ),
              const SizedBox(width: 4),
              const Icon(Icons.unfold_more, size: 16, color: Palette.faintSlate),
            ],
          ),
        ),
      ),
    );
  }
}

/// A row inside a panel that folds content open beneath it (no card of its own).
class FoldRow extends StatefulWidget {
  const FoldRow({super.key, required this.title, required this.child, this.first = false});

  final String title;
  final Widget child;
  final bool first;

  @override
  State<FoldRow> createState() => _FoldRowState();
}

class _FoldRowState extends State<FoldRow> {
  var _open = false;

  @override
  Widget build(BuildContext context) {
    final still = MediaQuery.of(context).disableAnimations;
    return AnimatedSize(
      duration: still ? Duration.zero : const Duration(milliseconds: 240),
      curve: const Cubic(0.16, 1, 0.3, 1),
      alignment: Alignment.topCenter,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Pressable(
            onTap: () => setState(() => _open = !_open),
            child: Container(
              constraints: const BoxConstraints(minHeight: 46),
              decoration: BoxDecoration(
                border: widget.first ? null : const Border(top: BorderSide(color: Palette.hairlineSoft)),
              ),
              child: Row(
                children: [
                  Expanded(child: Text(widget.title, style: AppText.body)),
                  AnimatedRotation(
                    turns: _open ? .5 : 0,
                    duration: still ? Duration.zero : const Duration(milliseconds: 240),
                    child: const Icon(Icons.expand_more, size: 18, color: Palette.faintSlate),
                  ),
                ],
              ),
            ),
          ),
          if (_open) widget.child,
        ],
      ),
    );
  }
}

/// Questions to tap (Ask's starters and follow-ups, the coaches' quick questions): rows in
/// one panel, an optional kind on the left, an arrow on the right. [rows] are
/// (key, kind, question); a null [onTap] disables them (while an answer streams).
class SuggestionRows extends StatelessWidget {
  const SuggestionRows({super.key, required this.rows, required this.onTap, this.title});

  final String? title;
  final List<(Key, String?, String)> rows;
  final ValueChanged<String>? onTap;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      if (title != null)
        Padding(
          padding: const EdgeInsets.only(bottom: Space.xs),
          child: Text(title!, style: AppText.label.copyWith(color: Palette.mutedSlate)),
        ),
      Card(
        child: Column(
          children: [
            for (final (i, (key, kind, q)) in rows.indexed)
              Pressable(
                key: key,
                onTap: onTap == null ? null : () => onTap!(q),
                child: Opacity(
                  opacity: onTap == null ? .5 : 1,
                  child: Container(
                    constraints: const BoxConstraints(minHeight: 46),
                    padding: const EdgeInsets.symmetric(horizontal: Space.md, vertical: 10),
                    decoration: BoxDecoration(
                      border: i == 0 ? null : const Border(top: BorderSide(color: Palette.hairlineSoft)),
                    ),
                    child: Row(
                      children: [
                        if (kind != null)
                          SizedBox(
                            width: 60,
                            child: Text(kind, style: AppText.readout.copyWith(fontSize: 10.5, color: Palette.mutedSlate)),
                          ),
                        Expanded(child: Text(q, style: AppText.body.copyWith(color: Palette.instrumentInk))),
                        const SizedBox(width: Space.xs),
                        const Icon(Icons.arrow_forward, size: 16, color: Palette.faintSlate),
                      ],
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    ],
  );
}

/// A question as asked, above its answer in a conversation (the coaches).
class QuestionBubble extends StatelessWidget {
  const QuestionBubble(this.text, {super.key});

  final String text;

  @override
  Widget build(BuildContext context) => Align(
    alignment: Alignment.centerRight,
    child: Container(
      margin: const EdgeInsets.only(left: 48, bottom: Space.sm),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(color: Palette.insetGray, borderRadius: BorderRadius.circular(Radii.control)),
      child: Text(text, style: AppText.body.copyWith(color: Palette.instrumentInk)),
    ),
  );
}
