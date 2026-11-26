from pathlib import Path

root = Path("astro_mobile")
main = root / "lib/main.dart"
account = root / "lib/screens/account_screen.dart"
service = root / "lib/services/astro_analytics_service.dart"

if not main.exists() or not account.exists():
    raise SystemExit("Expected Flutter source files were not found")

service.write_text("""import 'dart:math';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

class AstroAnalyticsService {
  static const _installationKey = 'astro_mobile_analytics_installation_id';
  static const _firstOpenKey = 'astro_mobile_first_open_recorded';

  static Future<String> installationId() async {
    final prefs = await SharedPreferences.getInstance();
    var id = prefs.getString(_installationKey);
    if (id == null || id.length < 8) {
      final random = Random.secure();
      final suffix = List.generate(24, (_) => random.nextInt(16).toRadixString(16)).join();
      id = 'astro-$suffix';
      await prefs.setString(_installationKey, id);
    }
    return id;
  }

  static Future<void> recordFirstOpen() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      if (prefs.getBool(_firstOpenKey) == true) return;
      final id = await installationId();
      try {
        await Supabase.instance.client.from('astro_analytics_events').insert({
          'event_name': 'app_first_open',
          'installation_id': id,
          'source': 'android_app',
          'metadata': {'app_version': '1.2.0+3'},
        });
      } catch (error) {
        // A duplicate means this installation was already counted.
        final message = error.toString().toLowerCase();
        if (!message.contains('duplicate') && !message.contains('23505')) rethrow;
      }
      await prefs.setBool(_firstOpenKey, true);
    } catch (error) {
      debugPrint('ASTRO analytics first-open event failed: $error');
    }
  }
}
""")

text = main.read_text()
if "astro_analytics_service.dart" not in text:
    text = text.replace("import 'services/cart_service.dart';", "import 'services/cart_service.dart';\nimport 'services/astro_analytics_service.dart';")
if "AstroAnalyticsService.recordFirstOpen()" not in text:
    text = text.replace("  try {\n    await NotificationService.instance.initialize();", "  await AstroAnalyticsService.recordFirstOpen();\n\n  try {\n    await NotificationService.instance.initialize();")
main.write_text(text)

text = account.read_text()
if "astro_analytics_service.dart" not in text:
    text = text.replace("import '../", "import '../", 1)
    # Insert alongside the existing relative imports.
    lines = text.splitlines()
    insert_at = next((i for i, line in enumerate(lines) if line.startswith("import ")), 0)
    lines.insert(insert_at, "import '../services/astro_analytics_service.dart';")
    text = "\n".join(lines) + "\n"
text = text.replace("'phone': _normalizedPhone(),", "'phone': _normalizedPhone(),\n            'astro_installation_id': await AstroAnalyticsService.installationId(),")
account.write_text(text)
print("Patched app first-open tracking and registration-to-installation attribution.")
