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
if "_bindAuthenticatedUser()" not in s:
    s = s.replace(marker, method + marker, 1)

p.write_text(s, encoding="utf-8")
print("Automatic FCM registration on authenticated session added.")
