import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'app.dart';
import 'data/server.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  LicenseRegistry.addLicense(() async* {
    for (final (family, file) in [
      ('Chakra Petch', 'ChakraPetch'),
      ('Space Grotesk', 'SpaceGrotesk'),
      ('JetBrains Mono', 'JetBrainsMono'),
    ]) {
      yield LicenseEntryWithLineBreaks([family], await rootBundle.loadString('assets/fonts/$file-OFL.txt'));
    }
  });
  final prefs = await SharedPreferences.getInstance();
  final start = prefs.getString('start_route');
  if (start != null) await prefs.remove('start_route');
  runApp(ProviderScope(
    // A failed request shows the can't-reach state at once; the user retries, not a timer.
    retry: (_, _) => null,
    overrides: [prefsProvider.overrideWithValue(prefs)],
    // A one-shot start page for the README video's capture (tools/video/capture-app.mjs
    // writes it with `simctl spawn … defaults write`); read once, then cleared.
    child: PokeragApp(initialLocation: start),
  ));
}
