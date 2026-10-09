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
  runApp(ProviderScope(
    // A failed request shows the can't-reach state at once; the user retries, not a timer.
    retry: (_, _) => null,
    overrides: [prefsProvider.overrideWithValue(prefs)],
    child: const PokeragApp(),
  ));
}
