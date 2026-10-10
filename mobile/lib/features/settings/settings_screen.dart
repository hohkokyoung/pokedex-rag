import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../data/server.dart';
import '../../theme/theme.dart';
import '../../theme/tokens.g.dart';
import '../../widgets/ui.dart';

/// Where the app finds your pokérag server. An address is saved only after its
/// `/health` answers, so a typo never strands the app.
class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  late final _field = TextEditingController(text: ref.read(serverAddressProvider));
  String? _problem;
  bool _checking = false;

  @override
  void dispose() {
    _field.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    setState(() {
      _checking = true;
      _problem = null;
    });
    final problem = await ref.read(serverAddressProvider.notifier).save(_field.text);
    if (!mounted) return;
    setState(() {
      _checking = false;
      _problem = problem;
    });
    if (problem == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Connected. Loading the Pokédex.')));
      context.canPop() ? context.pop() : context.go('/');
    }
  }

  @override
  Widget build(BuildContext context) {
    final current = ref.watch(serverAddressProvider);
    return Scaffold(
      appBar: pageBar('Server'),
      body: ListView(
        padding: const EdgeInsets.all(Space.gutter),
        children: [
          Text('pokérag reads everything from your own server on this Wi-Fi.', style: AppText.body),
          const SizedBox(height: Space.lg),
          TextField(
            key: const Key('address'),
            controller: _field,
            keyboardType: TextInputType.url,
            autocorrect: false,
            enabled: !_checking,
            onSubmitted: (_) => _save(),
            decoration: InputDecoration(
              labelText: 'Server address',
              hintText: 'http://192.168.0.10:8001',
              errorText: _problem,
              errorMaxLines: 3,
            ),
          ),
          const SizedBox(height: Space.md),
          FilledButton(
            key: const Key('save'),
            onPressed: _checking ? null : _save,
            child: Text(_checking ? 'Checking…' : 'Check and save'),
          ),
          const SizedBox(height: Space.lg),
          Text('Now using', style: AppText.label.copyWith(color: Palette.mutedSlate)),
          const SizedBox(height: Space.xs),
          Text(current, style: AppText.readout),
          if (current != defaultAddress) ...[
            const SizedBox(height: Space.sm),
            Align(
              alignment: Alignment.centerLeft,
              child: TextButton(
                onPressed: () async {
                  await ref.read(serverAddressProvider.notifier).reset();
                  _field.text = defaultAddress;
                },
                child: Text('Use the default ($defaultAddress)'),
              ),
            ),
          ],
          const SizedBox(height: Space.lg),
          Text(
            "On a phone, use your Mac's Wi-Fi address with port 8001. "
            'The Simulator can use http://localhost:8001.',
            style: AppText.bodySmall.copyWith(color: Palette.mutedSlate),
          ),
        ],
      ),
    );
  }
}
