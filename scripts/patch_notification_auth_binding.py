from pathlib import Path

p = Path("astro_mobile/lib/services/notification_service.dart")
s = p.read_text(encoding="utf-8")

if "import 'dart:async';" not in s:
    s = s.replace("import 'dart:convert';", "import 'dart:async';\nimport 'dart:convert';", 1)

if "_authSubscription" not in s:
    s = s.replace(
        "  String? _lastPhone;\n",
        "  String? _lastPhone;\n  StreamSubscription<AuthState>? _authSubscription;\n",
        1,
    )

old = """    final prefs = await SharedPreferences.getInstance();
    _lastPhone = prefs.getString(_phoneKey);

    FirebaseMessaging.instance.onTokenRefresh.listen((token) async {"""
new = """    final prefs = await SharedPreferences.getInstance();
    _lastPhone = prefs.getString(_phoneKey);

    // Bind the Firebase device token automatically to every authenticated
    // customer account. The phone is stored in Supabase Auth user metadata
    // during sign-up, so customers do not need to log out and back in.
    _authSubscription ??= Supabase.instance.client.auth.onAuthStateChange.listen(
      (authState) async {
        final event = authState.event;
        if (event == AuthChangeEvent.signedIn ||
            event == AuthChangeEvent.initialSession ||
            event == AuthChangeEvent.tokenRefreshed ||
            event == AuthChangeEvent.userUpdated) {
          await _bindAuthenticatedUser();
        } else if (event == AuthChangeEvent.signedOut) {
          _lastPhone = null;
          final localPrefs = await SharedPreferences.getInstance();
          await localPrefs.remove(_phoneKey);
        }
      },
    );

    await _bindAuthenticatedUser();

    FirebaseMessaging.instance.onTokenRefresh.listen((token) async {"""
if old not in s:
    raise SystemExit("Could not find notification initialization insertion point")
s = s.replace(old, new, 1)

marker = "  Future<void> bindCurrentCustomerPhone(String phone) async {"
method = """  Future<void> _bindAuthenticatedUser() async {
    final user = Supabase.instance.client.auth.currentUser;
    if (user == null) return;
    final phone = user.userMetadata?['phone']?.toString().trim() ?? '';
    if (phone.isEmpty) return;
    await bindCurrentCustomerPhone(phone);
  }

"""
if "Future<void> _bindAuthenticatedUser()" not in s:
    s = s.replace(marker, method + marker, 1)


start = s.find("  Future<void> bindCurrentCustomerPhone(String phone) async {")
end = s.find("\n  Future<void> _registerToken(", start)
if start < 0 or end < 0:
    raise SystemExit("Could not locate FCM binding methods")
s = s[:start] + """  Future<String> bindCurrentCustomerPhone(String phone) async {
    final normalized = phone.trim();
    if (normalized.isEmpty) return 'رقم الهاتف غير متوفر في الحساب.';

    final user = Supabase.instance.client.auth.currentUser;
    if (user == null) return 'تعذر ربط الإشعارات: الحساب غير مسجل الدخول.';

    _lastPhone = normalized;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_phoneKey, normalized);

    String token;
    try {
      final value = await FirebaseMessaging.instance.getToken();
      if (value == null || value.isEmpty) {
        return 'تعذر الحصول على رمز Firebase. تحقق من خدمات Google على الهاتف.';
      }
      token = value;
    } on FirebaseException catch (e) {
      debugPrint('ASTRO FCM token error: ${e.code}');
      return 'فشل الحصول على رمز Firebase (${e.code}).';
    } catch (e) {
      debugPrint('ASTRO FCM token error: $e');
      return 'حدث خطأ أثناء استخراج رمز الإشعارات.';
    }

    return await _registerToken(token, normalized);
  }
""" + s[end:]

start = s.find("  Future<void> _registerToken(String token, String phone) async {")
end = s.find("\\n  Future<void> _showForeground(", start)
if start < 0 or end < 0:
    raise SystemExit("Could not locate FCM server registration method")
s = s[:start] + """  Future<String> _registerToken(String token, String phone) async {
    try {
      final response = await Supabase.instance.client.functions.invoke(
        'fcm-notifications',
        body: {
          'action': 'register',
          'phone': phone,
          'token': token,
          'platform': defaultTargetPlatform.name,
        },
      );
      final data = response.data;
      if (data is Map && data['success'] == true) {
        debugPrint('ASTRO FCM: server confirmed device registration.');
        return 'تم تسجيل جهازك لاستقبال الإشعارات بنجاح.';
      }
      debugPrint('ASTRO FCM: unexpected registration response: ${data.runtimeType}');
      return 'وصل الطلب إلى الخادم لكن لم يؤكد تسجيل الجهاز.';
    } on FunctionException catch (e) {
      debugPrint('ASTRO FCM registration server error: ${e.status}');
      return 'الخادم رفض تسجيل الإشعارات (HTTP ${e.status}).';
    } catch (e) {
      debugPrint('ASTRO FCM registration request error: $e');
      return 'تعذر الاتصال بخادم تسجيل الإشعارات.';
    }
  }
""" + s[end:]

p.write_text(s, encoding="utf-8")
print("Automatic FCM registration on authenticated session added.")

# Explicitly register the device after the account screen completes login or
# signup. This avoids relying only on an auth stream event during app startup.
account = Path("astro_mobile/lib/screens/account_screen.dart")
account_source = account.read_text(encoding="utf-8")
import_line = "import '../services/notification_service.dart';"
if import_line not in account_source:
    anchor = "import '../main.dart';"
    if anchor not in account_source:
        raise SystemExit("Could not find account screen service import anchor")
    account_source = account_source.replace(anchor, anchor + "\n" + import_line, 1)

call = """      final notificationStatus =
          await NotificationService.instance.bindCurrentCustomerPhone(_normalizedPhone());
      _message(notificationStatus);"""
if call not in account_source:
    anchor = "      if (mounted) setState(() {});"
    if anchor not in account_source:
        raise SystemExit("Could not find account submit completion anchor")
    account_source = account_source.replace(anchor, call + "\n" + anchor, 1)
account.write_text(account_source, encoding="utf-8")
print("Explicit FCM registration after account login/signup added.")

