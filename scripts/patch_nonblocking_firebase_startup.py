from pathlib import Path

path = Path("astro_mobile/lib/main.dart")
source = path.read_text()

old = """  await AstroAnalyticsService.recordFirstOpen();

  try {
    await NotificationService.instance.initialize();
  } catch (e) {
    debugPrint('ASTRO notifications initialization failed: $e');
  }

  runApp(const AstroMobileApp());
}"""

new = """  // Launch the store as soon as its essential backend is ready.
  // Analytics and FCM registration are deliberately non-blocking so a
  // temporary Google Play services / FCM delay can never hold the splash
  // screen or prevent customers from opening the store.
  runApp(const AstroMobileApp());

  unawaited(_initializeBackgroundServices());
}

Future<void> _initializeBackgroundServices() async {
  // These services are best-effort and must never delay or stop the UI.
  try {
    await AstroAnalyticsService.recordFirstOpen()
        .timeout(const Duration(seconds: 8));
  } catch (e) {
    debugPrint('ASTRO analytics initialization skipped: $e');
  }

  try {
    await NotificationService.instance.initialize()
        .timeout(const Duration(seconds: 12));
  } catch (e) {
    debugPrint('ASTRO notifications initialization continues in background: $e');
  }
}"""

if old not in source:
    raise SystemExit("Expected startup block was not found; refusing to modify main.dart.")

if "import 'dart:async';" not in source:
    source = "import 'dart:async';\n" + source

source = source.replace(old, new, 1)
if "runApp(const AstroMobileApp());\n\n  unawaited(_initializeBackgroundServices());" not in source:
    raise SystemExit("Non-blocking startup verification failed.")
if "await NotificationService.instance.initialize()" in source.split("void main()")[1].split("class AstroMobileApp")[0]:
    raise SystemExit("FCM initialization is still awaited inside main().")

path.write_text(source)
print("Startup patch applied: app UI starts before analytics and FCM.")
