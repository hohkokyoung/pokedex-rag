import 'package:flutter/material.dart';

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
      scaffoldBackgroundColor: Palette.ground,
      fontFamily: 'Space Grotesk',
      textTheme: TextTheme(
        displaySmall: AppText.display,
        headlineSmall: AppText.headline,
        titleMedium: AppText.title,
        bodyMedium: AppText.body,
        bodySmall: AppText.bodySmall,
        labelMedium: AppText.label,
      ).apply(bodyColor: Palette.instrumentInk, displayColor: Palette.instrumentInk),
      appBarTheme: const AppBarTheme(
        backgroundColor: Palette.ground,
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
        side: const BorderSide(color: Palette.hairline),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(Radii.control)),
        labelStyle: AppText.label.copyWith(
          fontSize: 14,
          color: WidgetStateColor.resolveWith(
            (states) => states.contains(WidgetState.selected) ? Palette.panelWhite : Palette.inkDim,
          ),
        ),
        iconTheme: const IconThemeData(color: Palette.pokeballRed, size: 16),
      ),
      dividerColor: Palette.hairline,
    );
  }
}

/// The type scale with the variable-font weight axis set, so Space Grotesk and
/// JetBrains Mono render at the weight DESIGN.md asks for.
abstract final class AppText {
  static final display = _v(TypeScale.display);
  static final headline = _v(TypeScale.headline);
  static final title = _v(TypeScale.title);
  static final body = _v(TypeScale.body);
  static final bodySmall = _v(TypeScale.bodySmall);
  static final label = _v(TypeScale.label);
  static final readout = _v(TypeScale.readout);

  static TextStyle _v(TextStyle s) =>
      s.copyWith(fontVariations: [FontVariation.weight((s.fontWeight ?? FontWeight.w400).value.toDouble())]);
}
