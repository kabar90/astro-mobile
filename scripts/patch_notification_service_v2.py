from pathlib import Path
target = Path("astro_mobile/lib/services/notification_service.dart")
if not target.exists(): raise SystemExit("Notification service source was not found")
source = r'''import 'dart:async';
import 'dart:convert';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

const AndroidNotificationChannel _astroChannel = AndroidNotificationChannel(
  'astro_mobile_notifications', 'ASTRO MOBILE',
  description: 'إشعارات الطلبات والعروض من ASTRO MOBILE',
  importance: Importance.high,
);

@pragma('vm:entry-point')
Future<void> astroFirebaseBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
}

class NotificationService {
  NotificationService._();
  static final NotificationService instance = NotificationService._();
  static const String _historyKey = 'astro_notification_history';
  static const String _phoneKey = 'astro_notification_phone';
  final FlutterLocalNotificationsPlugin _local = FlutterLocalNotificationsPlugin();

  bool _initialized = false;
  bool _localReady = false;
  bool _tokenWorkRunning = false;
  String? _activePhone;
  StreamSubscription<AuthState>? _authSubscription;
  StreamSubscription<RemoteMessage>? _foregroundSubscription;
  StreamSubscription<RemoteMessage>? _openedSubscription;

  /// Firebase listeners initialize independently of token registration.
  Future<void> initialize() async {
    if (_initialized) return;
    await Firebase.initializeApp();
    FirebaseMessaging.onBackgroundMessage(astroFirebaseBackgroundHandler);

    const settings = InitializationSettings(
      android: AndroidInitializationSettings('@mipmap/ic_launcher'),
    );
    await _local.initialize(settings);
    final android = _local.resolvePlatformSpecificImplementation<
        AndroidFlutterLocalNotificationsPlugin>();
    await android?.createNotificationChannel(_astroChannel);
    _localReady = true;

    FirebaseMessaging.instance.onTokenRefresh.listen((token) {
      final phone = _activePhone;
      if (phone != null && phone.isNotEmpty) {
        unawaited(_registerToken(token, phone));
      }
    });
    _foregroundSubscription = FirebaseMessaging.onMessage.listen(_showForeground);
    _openedSubscription = FirebaseMessaging.onMessageOpenedApp.listen(_recordMessage);

    _authSubscription = Supabase.instance.client.auth.onAuthStateChange.listen((state) {
      switch (state.event) {
        case AuthChangeEvent.signedIn:
        case AuthChangeEvent.initialSession:
        case AuthChangeEvent.tokenRefreshed:
        case AuthChangeEvent.userUpdated:
          unawaited(_bindAuthenticatedUser());
          break;
        case AuthChangeEvent.signedOut:
          _activePhone = null;
          unawaited(_clearLocalPhone());
          break;
        default:
          break;
      }
    });

    _initialized = true;
    unawaited(_requestPermissionAndBind());
    final initial = await FirebaseMessaging.instance.getInitialMessage();
    if (initial != null) unawaited(_recordMessage(initial));
  }

  Future<void> _requestPermissionAndBind() async {
    try {
      await FirebaseMessaging.instance.requestPermission(
        alert: true, badge: true, sound: true,
      );
    } catch (e) {
      debugPrint('ASTRO FCM permission request failed: $e');
    }
    await _bindAuthenticatedUser();
  }

  Future<void> _bindAuthenticatedUser() async {
    final user = Supabase.instance.client.auth.currentUser;
    if (user == null) return;
    final phone = user.userMetadata?['phone']?.toString().trim() ?? '';
    if (phone.isEmpty) {
      debugPrint('ASTRO FCM: authenticated user has no phone metadata.');
      return;
    }
    await bindCurrentCustomerPhone(phone);
  }

  /// Compatibility method retained for account and checkout screens.
  Future<String> bindCurrentCustomerPhone(String phone) async {
    final normalized = phone.trim();
    if (normalized.isEmpty) return 'رقم الهاتف غير متوفر.';
    if (Supabase.instance.client.auth.currentUser == null) {
      return 'يجب تسجيل الدخول أولاً.';
    }
    _activePhone = normalized;
    if (_tokenWorkRunning) return 'جاري تجهيز إشعارات جهازك.';
    unawaited(_acquireAndRegisterToken(normalized));
    return 'بدأ تسجيل جهازك لاستقبال الإشعارات.';
  }

  Future<void> _acquireAndRegisterToken(String phone) async {
    if (_tokenWorkRunning) return;
    _tokenWorkRunning = true;
    try {
      try {
        await FirebaseMessaging.instance.setAutoInitEnabled(true);
      } catch (e) {
        debugPrint('ASTRO FCM auto-init warning: $e');
      }

      // Report the Firebase configuration loaded at runtime, without exposing secrets.
      final options = Firebase.app().options;
      final runtimeConfig = 'projectId=${options.projectId}; '
          'appId=${options.appId}; '
          'senderId=${options.messagingSenderId}; '
          'apiKeyPresent=${options.apiKey.isNotEmpty}';
      await _diagnostic(phone, 'firebase_runtime_config', 0, runtimeConfig);

      String? token;
      Object? lastError;
      const waits = [0, 5, 15];
      for (var i = 0; i < waits.length; i++) {
        if (waits[i] > 0) await Future.delayed(Duration(seconds: waits[i]));
        try {
          token = await FirebaseMessaging.instance.getToken()
              .timeout(const Duration(seconds: 25));
          if (token != null && token!.trim().isNotEmpty) break;
          lastError = StateError('Firebase returned an empty FCM token.');
        } catch (e) {
          lastError = e;
          debugPrint('ASTRO FCM getToken attempt ${i + 1} failed: $e');
          await _diagnostic(phone, 'get_token_failed', i + 1, e.toString());
        }
      }
      if (token == null || token!.trim().isEmpty) {
        await _diagnostic(phone, 'get_token_exhausted', 3,
            lastError?.toString() ?? 'No token returned');
        debugPrint('ASTRO FCM: token unavailable after retries.');
        return;
      }

      try {
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString(_phoneKey, phone);
      } catch (e) {
        debugPrint('ASTRO FCM local phone cache skipped: $e');
      }
      await _registerToken(token!, phone);
    } finally {
      _tokenWorkRunning = false;
    }
  }

  Future<void> _diagnostic(String phone, String stage, int attempt, String error) async {
    try {
      final user = Supabase.instance.client.auth.currentUser;
      final digits = phone.replaceAll(RegExp(r'\D'), '');
      await Supabase.instance.client.functions.invoke('fcm-notifications', body: {
        'action': 'diagnostic',
        'user_id': user?.id,
        'phone_suffix': digits.length >= 4 ? digits.substring(digits.length - 4) : 'unknown',
        'stage': stage,
        'attempt': attempt,
        'error': error.length > 500 ? error.substring(0, 500) : error,
        'platform': defaultTargetPlatform.name,
      });
    } catch (e) {
      debugPrint('ASTRO FCM diagnostic upload failed: $e');
    }
  }

  Future<String> _registerToken(String token, String phone) async {
    try {
      final response = await Supabase.instance.client.functions.invoke(
        'fcm-notifications',
        body: {
          'action': 'register', 'phone': phone, 'token': token,
          'platform': defaultTargetPlatform.name,
        },
      );
      if (response.data is Map && response.data['success'] == true) {
        debugPrint('ASTRO FCM: device token registered.');
        return 'تم تسجيل جهازك لاستقبال الإشعارات بنجاح.';
      }
      debugPrint('ASTRO FCM registration response: ${response.data}');
      return 'لم يؤكد الخادم تسجيل جهازك.';
    } on FunctionException catch (e) {
      await _diagnostic(phone, 'server_register', 1,
          'HTTP ${e.status}: ${e.details ?? e.reasonPhrase ?? 'unknown'}');
      return 'تعذر تسجيل الجهاز لدى الخادم.';
    } catch (e) {
      await _diagnostic(phone, 'server_register', 1, e.toString());
      return 'تعذر الاتصال بخادم الإشعارات.';
    }
  }

  Future<void> _showForeground(RemoteMessage message) async {
    await _recordMessage(message);
    if (!_localReady) return;
    final title = message.notification?.title ??
        message.data['title']?.toString() ?? 'ASTRO MOBILE';
    final body = message.notification?.body ??
        message.data['body']?.toString() ?? 'لديك إشعار جديد';
    await _local.show(
      message.messageId?.hashCode ?? DateTime.now().millisecondsSinceEpoch,
      title, body,
      NotificationDetails(android: AndroidNotificationDetails(
        _astroChannel.id, _astroChannel.name,
        channelDescription: _astroChannel.description,
        importance: Importance.high, priority: Priority.high,
        icon: '@mipmap/ic_launcher',
      )),
    );
  }

  Future<void> _recordMessage(RemoteMessage message) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final rows = prefs.getStringList(_historyKey) ?? <String>[];
      rows.insert(0, jsonEncode({
        'title': message.notification?.title ??
            message.data['title']?.toString() ?? 'ASTRO MOBILE',
        'body': message.notification?.body ?? message.data['body']?.toString() ?? '',
        'date': DateTime.now().toIso8601String(),
      }));
      if (rows.length > 50) rows.removeRange(50, rows.length);
      await prefs.setStringList(_historyKey, rows);
    } catch (e) {
      debugPrint('ASTRO notification history save failed: $e');
    }
  }

  Future<List<Map<String, dynamic>>> history() async {
    final prefs = await SharedPreferences.getInstance();
    final rows = prefs.getStringList(_historyKey) ?? <String>[];
    return rows.map((value) => jsonDecode(value) as Map<String, dynamic>).toList();
  }

  Future<void> _clearLocalPhone() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_phoneKey);
    } catch (e) {
      debugPrint('ASTRO FCM local phone clear failed: $e');
    }
  }
}
'''
# Add a direct Firebase Installations probe so FIS can be tested independently
# from the FCM registration token request.
pubspec = Path("astro_mobile/pubspec.yaml")
pub = pubspec.read_text()
if "firebase_app_installations:" not in pub:
    anchor = "  firebase_core: ^4.15.2"
    if anchor not in pub:
        raise SystemExit("firebase_core dependency anchor missing")
    pub = pub.replace(anchor, anchor + "\n  firebase_app_installations: ^0.4.5", 1)
    pubspec.write_text(pub)

if "package:firebase_app_installations/firebase_app_installations.dart" not in source:
    source = source.replace(
        "import 'package:firebase_core/firebase_core.dart';",
        "import 'package:firebase_core/firebase_core.dart';\nimport 'package:firebase_app_installations/firebase_app_installations.dart';",
        1,
    )

probe = """      // Probe Firebase Installations separately from FCM token registration.
      try {
        final installationId = await FirebaseInstallations.instance
            .getId().timeout(const Duration(seconds: 20));
        await _diagnostic(phone, 'fis_get_id_success', 0,
            'installationIdPresent=${installationId.isNotEmpty}');
        final installationToken = await FirebaseInstallations.instance
            .getToken().timeout(const Duration(seconds: 20));
        await _diagnostic(phone, 'fis_auth_token_success', 0,
            'installationTokenPresent=${installationToken.isNotEmpty}');
      } catch (e) {
        await _diagnostic(phone, 'fis_probe_failed', 0, e.toString());
        debugPrint('ASTRO Firebase Installations probe failed: $e');
      }

      String? token;"""
if "Probe Firebase Installations separately from FCM token registration." not in source:
    source = source.replace("      String? token;", probe, 1)

target.write_text(source)
print("Rebuilt notification_service.dart")
