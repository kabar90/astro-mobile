from pathlib import Path
target = Path("astro_mobile/lib/services/notification_service.dart")
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
  final FlutterLocalNotificationsPlugin _local = FlutterLocalNotificationsPlugin();
  static const String _historyKey = 'astro_notification_history';
  bool _ready = false;
  Future<void>? _initializing;
  Future<String>? _binding;
  StreamSubscription<AuthState>? _authSubscription;
  StreamSubscription<String>? _tokenSubscription;
  StreamSubscription<RemoteMessage>? _foregroundSubscription;
  StreamSubscription<RemoteMessage>? _openedSubscription;

  Future<void> initialize() {
    if (_ready) return Future<void>.value();
    final running = _initializing;
    if (running != null) return running;
    final task = _initializeOnce();
    _initializing = task;
    return task.whenComplete(() {
      if (identical(_initializing, task)) _initializing = null;
    });
  }

  Future<void> _initializeOnce() async {
    await Firebase.initializeApp();
    FirebaseMessaging.onBackgroundMessage(astroFirebaseBackgroundHandler);
    const settings = InitializationSettings(android: AndroidInitializationSettings('@mipmap/ic_launcher'));
    await _local.initialize(settings);
    final android = _local.resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>();
    await android?.createNotificationChannel(_astroChannel);

    try {
      await FirebaseMessaging.instance.requestPermission(alert: true, badge: true, sound: true);
    } catch (error) {
      debugPrint('ASTRO FCM permission request failed: $error');
    }

    _foregroundSubscription ??= FirebaseMessaging.onMessage.listen(_showForeground);
    _openedSubscription ??= FirebaseMessaging.onMessageOpenedApp.listen(_recordMessage);
    _authSubscription ??= Supabase.instance.client.auth.onAuthStateChange.listen((state) {
      if (state.event == AuthChangeEvent.signedIn ||
          state.event == AuthChangeEvent.initialSession ||
          state.event == AuthChangeEvent.tokenRefreshed ||
          state.event == AuthChangeEvent.userUpdated) {
        unawaited(_bindAuthenticatedUser());
      }
    });
    _tokenSubscription ??= FirebaseMessaging.instance.onTokenRefresh.listen(
      (token) => unawaited(_registerForCurrentUser(token)),
      onError: (Object error) => debugPrint('ASTRO FCM token refresh error: $error'),
    );

    _ready = true;
    unawaited(_bindAuthenticatedUser());
    try {
      final initial = await FirebaseMessaging.instance.getInitialMessage();
      if (initial != null) await _recordMessage(initial);
    } catch (error) {
      debugPrint('ASTRO FCM initial message check skipped: $error');
    }
  }

  Future<void> _bindAuthenticatedUser() async {
    final user = Supabase.instance.client.auth.currentUser;
    if (user == null) return;
    final phone = user.userMetadata?['phone']?.toString().trim() ?? '';
    if (phone.isEmpty) {
      debugPrint('ASTRO FCM: signed-in account has no phone metadata.');
      return;
    }
    await bindCurrentCustomerPhone(phone);
  }

  // Public API retained for compatibility with account_screen.dart.
  Future<String> bindCurrentCustomerPhone(String phone) {
    final normalized = phone.trim();
    if (normalized.isEmpty) return Future<String>.value('رقم الهاتف غير متوفر في الحساب.');
    final user = Supabase.instance.client.auth.currentUser;
    if (user == null) return Future<String>.value('تعذر ربط الإشعارات: الحساب غير مسجل الدخول.');
    final running = _binding;
    if (running != null) return running;
    final task = _bindDevice(normalized, user.id);
    _binding = task;
    return task.whenComplete(() {
      if (identical(_binding, task)) _binding = null;
    });
  }

  Future<String> _bindDevice(String phone, String userId) async {
    String? token;
    Object? lastError;
    for (var attempt = 1; attempt <= 3; attempt++) {
      try {
        await FirebaseMessaging.instance.setAutoInitEnabled(true).timeout(const Duration(seconds: 8));
        token = await FirebaseMessaging.instance.getToken().timeout(const Duration(seconds: 15));
        if (token != null && token.isNotEmpty) break;
        lastError = StateError('Firebase returned an empty FCM token.');
      } catch (error) {
        lastError = error;
        debugPrint('ASTRO FCM getToken attempt $attempt failed: $error');
        await _reportDiagnostic(phone: phone, stage: 'getToken_attempt_failed',
          attempt: attempt, error: error.toString(), userId: userId);
      }
      if (attempt < 3) await Future<void>.delayed(Duration(seconds: attempt * 2));
    }
    if (token == null || token.isEmpty) {
      final detail = lastError?.toString() ?? 'No token returned';
      await _reportDiagnostic(phone: phone, stage: 'getToken_failed',
        attempt: 3, error: detail, userId: userId);
      return 'تعذر استخراج رمز الإشعارات: $detail';
    }
    return _registerToken(token, phone, userId);
  }

  Future<void> _registerForCurrentUser(String token) async {
    final user = Supabase.instance.client.auth.currentUser;
    if (user == null) return;
    final phone = user.userMetadata?['phone']?.toString().trim() ?? '';
    if (phone.isEmpty) return;
    await _registerToken(token, phone, user.id);
  }

  Future<void> _reportDiagnostic({
    required String phone, required String stage, required int attempt,
    required String error, required String userId,
  }) async {
    try {
      final digits = phone.replaceAll(RegExp(r'\D'), '');
      await Supabase.instance.client.functions.invoke('fcm-notifications', body: {
        'action': 'diagnostic', 'user_id': userId,
        'phone_suffix': digits.length >= 4 ? digits.substring(digits.length - 4) : 'unknown',
        'stage': stage, 'attempt': attempt,
        'error': error.length > 500 ? error.substring(0, 500) : error,
        'platform': defaultTargetPlatform.name,
      }).timeout(const Duration(seconds: 5));
    } catch (error) {
      debugPrint('ASTRO FCM diagnostic upload skipped: $error');
    }
  }

  Future<String> _registerToken(String token, String phone, String userId) async {
    final currentUser = Supabase.instance.client.auth.currentUser;
    if (currentUser == null || currentUser.id != userId) {
      return 'تم تغيير الحساب؛ أعد تسجيل الدخول لتفعيل الإشعارات.';
    }
    try {
      final response = await Supabase.instance.client.functions.invoke('fcm-notifications', body: {
        'action': 'register', 'phone': phone, 'token': token,
        'platform': defaultTargetPlatform.name,
      }).timeout(const Duration(seconds: 12));
      final data = response.data;
      if (data is Map && data['success'] == true) {
        debugPrint('ASTRO FCM: device token registered successfully.');
        return 'تم تسجيل جهازك لاستقبال الإشعارات بنجاح.';
      }
      debugPrint('ASTRO FCM: unexpected registration response: $data');
      return 'وصل الطلب إلى الخادم لكن لم يؤكد تسجيل الجهاز.';
    } on FunctionException catch (error) {
      debugPrint('ASTRO FCM registration rejected: HTTP ${error.status}');
      await _reportDiagnostic(phone: phone, stage: 'server_register', attempt: 1,
        error: 'HTTP ${error.status}: ${error.details ?? error.reasonPhrase ?? 'unknown'}',
        userId: userId);
      return 'الخادم رفض تسجيل الإشعارات (HTTP ${error.status}).';
    } catch (error) {
      debugPrint('ASTRO FCM registration request failed: $error');
      await _reportDiagnostic(phone: phone, stage: 'server_register', attempt: 1,
        error: error.toString(), userId: userId);
      return 'تعذر الاتصال بخادم تسجيل الإشعارات.';
    }
  }

  Future<void> _showForeground(RemoteMessage message) async {
    await _recordMessage(message);
    final title = message.notification?.title ?? message.data['title']?.toString() ?? 'ASTRO MOBILE';
    final body = message.notification?.body ?? message.data['body']?.toString() ?? 'لديك إشعار جديد';
    await _local.show(
      message.messageId?.hashCode ?? DateTime.now().millisecondsSinceEpoch,
      title, body,
      NotificationDetails(android: AndroidNotificationDetails(
        _astroChannel.id, _astroChannel.name,
        channelDescription: _astroChannel.description,
        importance: Importance.high, priority: Priority.high, icon: '@mipmap/ic_launcher',
      )),
    );
  }

  Future<void> _recordMessage(RemoteMessage message) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final rows = prefs.getStringList(_historyKey) ?? <String>[];
      rows.insert(0, jsonEncode({
        'title': message.notification?.title ?? message.data['title']?.toString() ?? 'ASTRO MOBILE',
        'body': message.notification?.body ?? message.data['body']?.toString() ?? '',
        'date': DateTime.now().toIso8601String(),
      }));
      if (rows.length > 50) rows.removeRange(50, rows.length);
      await prefs.setStringList(_historyKey, rows);
    } catch (error) {
      debugPrint('ASTRO notification history save failed: $error');
    }
  }

  Future<List<Map<String, dynamic>>> history() async {
    final prefs = await SharedPreferences.getInstance();
    final rows = prefs.getStringList(_historyKey) ?? <String>[];
    return rows.map((row) => jsonDecode(row) as Map<String, dynamic>).toList();
  }
}
'''
target.write_text(source, encoding="utf-8")
print("Replaced notification service with isolated, non-blocking FCM lifecycle.")
