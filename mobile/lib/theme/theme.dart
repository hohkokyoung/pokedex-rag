import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../widgets/ui.dart' show Ground;
import 'tokens.g.dart';

/// The light "Field Instrument" theme (DESIGN.md), built only from generated tokens.
abstract final class AppTheme {
  static ThemeData light() {
    final scheme = ColorScheme.fromSeed(seedColor: Palette.pokeballRed).copyWith(
      primary: Palette.pokeballRed,
      onPrimary: Palette.panelWhite,
      surface: Palette.panelWhite,
      onSurface: Palette.instrumentInk,
      onSurfaceVariant: Palette.mutedSlate,
      outline: Palette.hairline,
      outlineVariant: Palette.hairlineSoft,
      error: Palette.pokeballRedText,
    );
    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      scaffoldBackgroundColor: Colors.transparent, // the Ground gradient shows through
      fontFamily: 'Space Grotesk',
      textTheme: TextTheme(
        displaySmall: AppText.display,
        headlineSmall: AppText.headline,
        titleMedium: AppText.title,
        // Text fields use bodyLarge: keep them on the app's scale, not Material's 16.
        bodyLarge: AppText.body.copyWith(fontSize: 15, height: 1.35),
        bodyMedium: AppText.body,
        bodySmall: AppText.bodySmall,
        labelMedium: AppText.label,
      ).apply(bodyColor: Palette.instrumentInk, displayColor: Palette.instrumentInk),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        surfaceTintColor: Colors.transparent,
        // Dark status-bar icons and time on the light ground.
        systemOverlayStyle: SystemUiOverlayStyle.dark,
        foregroundColor: Palette.instrumentInk,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
      ),
      cardTheme: CardThemeData(
        color: Palette.panelWhite,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(Radii.card),
          side: const BorderSide(color: Palette.hairline),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Palette.panelWhite,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(Radii.control),
          borderSide: const BorderSide(color: Palette.hairline),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(Radii.control),
          borderSide: const BorderSide(color: Palette.hairline),
        ),
        // Focus darkens the hairline; no thick coloured Material outline.
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(Radii.control),
          borderSide: const BorderSide(color: Palette.mutedSlate),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: Palette.pokeballRed,
          foregroundColor: Palette.panelWhite,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(Radii.control)),
          textStyle: AppText.label,
        ),
      ),
      // Choices (sort, forms): ink when selected, like the website's active controls.
      chipTheme: ChipThemeData(
        backgroundColor: Palette.panelWhite,
        selectedColor: Palette.instrumentInk,
        showCheckmark: false,
        // Compact, as filters on a phone should be.
        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
        labelPadding: const EdgeInsets.symmetric(horizontal: 4),
        side: const BorderSide(color: Palette.hairline),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(Radii.control)),
        labelStyle: AppText.label.copyWith(
          fontSize: 13,
          color: WidgetStateColor.resolveWith(
            (states) => states.contains(WidgetState.selected) ? Palette.panelWhite : Palette.inkDim,
          ),
        ),
        iconTheme: const IconThemeData(color: Palette.pokeballRed, size: 16),
      ),
      // The tab bar: white with an inset-grey pill, ink when selected (no Material tint).
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: Palette.panelWhite,
        indicatorColor: Palette.insetGray,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        height: 64,
        iconTheme: WidgetStateProperty.resolveWith(
          (s) => IconThemeData(color: s.contains(WidgetState.selected) ? Palette.instrumentInk : Palette.mutedSlate),
        ),
        labelTextStyle: WidgetStateProperty.resolveWith(
          (s) => AppText.label.copyWith(color: s.contains(WidgetState.selected) ? Palette.instrumentInk : Palette.mutedSlate),
        ),
      ),
      // Dialogs, menus and sheets on white (no Material surface tint).
      dialogTheme: DialogThemeData(
        backgroundColor: Palette.panelWhite,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(Radii.card)),
      ),
      popupMenuTheme: PopupMenuThemeData(
        color: Palette.panelWhite,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(Radii.control),
          side: const BorderSide(color: Palette.hairline),
        ),
      ),
      // Every shape on the scale: 10 controls, 14 panels and sheets (no Material stadiums).
      bottomSheetTheme: const BottomSheetThemeData(
        backgroundColor: Palette.panelWhite,
        surfaceTintColor: Colors.transparent,
        dragHandleColor: Palette.hairline,
        dragHandleSize: Size(36, 4),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(Radii.card + 4))),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: Palette.instrumentInk,
          backgroundColor: Palette.panelWhite,
          side: const BorderSide(color: Palette.hairline),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(Radii.control)),
          textStyle: AppText.label.copyWith(fontSize: 13.5),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: Palette.pokeballRedText,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(Radii.control)),
          textStyle: AppText.label.copyWith(fontSize: 13.5),
        ),
      ),
      dividerColor: Palette.hairline,
      // iOS feel on every platform: no ink ripples (a pressed thing dims instead),
      // iOS page slides with swipe-back, and each page opaque so pages never show through.
      splashFactory: NoSplash.splashFactory,
      highlightColor: const Color(0x0A14171D),
      hoverColor: Colors.transparent,
      pageTransitionsTheme: const PageTransitionsTheme(
        builders: {
          TargetPlatform.iOS: _GroundedPages(),
          TargetPlatform.android: _GroundedPages(),
          TargetPlatform.macOS: _GroundedPages(),
        },
      ),
      textSelectionTheme: const TextSelectionThemeData(cursorColor: Palette.instrumentInk),
      // Sliders: a thin ink track and a round white knob, like iOS.
      sliderTheme: SliderThemeData(
        trackHeight: 4,
        activeTrackColor: Palette.instrumentInk,
        inactiveTrackColor: Palette.hairline,
        thumbColor: Palette.panelWhite,
        overlayColor: Colors.transparent,
        thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 13, elevation: 2, pressedElevation: 3),
        trackShape: const RoundedRectSliderTrackShape(),
        tickMarkShape: SliderTickMarkShape.noTickMark,
        showValueIndicator: ShowValueIndicator.never,
      ),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        backgroundColor: Palette.instrumentInk,
        contentTextStyle: AppText.bodySmall.copyWith(color: Palette.panelWhite),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(Radii.control)),
        elevation: 0,
      ),
    );
  }
}

/// The type scale with the variable-font weight axis set, so Space Grotesk and
/// JetBrains Mono render at the weight DESIGN.md asks for.
abstract final class AppText {
  // DESIGN.md's scale is for the website; Space Grotesk is wide, so on a phone every
  // step is a little smaller and body text a little tighter.
  static final display = _v(TypeScale.display);
  static final headline = _v(TypeScale.headline.copyWith(fontSize: 16.5));
  static final title = _v(TypeScale.title.copyWith(fontSize: 15));
  static final body = _v(TypeScale.body.copyWith(fontSize: 14, height: 1.45));
  static final bodySmall = _v(TypeScale.bodySmall.copyWith(fontSize: 12.5, height: 1.4));
  static final label = _v(TypeScale.label.copyWith(fontSize: 12));
  static final readout = _v(TypeScale.readout.copyWith(fontSize: 11));

  static TextStyle _v(TextStyle s) =>
      s.copyWith(fontVariations: [FontVariation.weight((s.fontWeight ?? FontWeight.w400).value.toDouble())]);
}

/// iOS page slides (with swipe-back), each page on its own ground.
class _GroundedPages extends PageTransitionsBuilder {
  const _GroundedPages();

  static const _ios = CupertinoPageTransitionsBuilder();

  @override
  Widget buildTransitions<T>(
    PageRoute<T> route,
    BuildContext context,
    Animation<double> animation,
    Animation<double> secondaryAnimation,
    Widget child,
  ) => _ios.buildTransitions(route, context, animation, secondaryAnimation, Ground(child: child));
}
