from pathlib import Path

root = Path("astro_mobile")

# Add durable local persistence for both normal products and inquiry options.
cart_path = root / "lib/services/cart_service.dart"
s = cart_path.read_text(encoding="utf-8")

if "import 'dart:convert';" not in s:
    s = s.replace(
        "import 'package:flutter/foundation.dart';",
        "import 'dart:convert';\nimport 'package:flutter/foundation.dart';\nimport 'package:shared_preferences/shared_preferences.dart';",
        1,
    )

line_anchor = "  double get total => price * quantity;\n"
line_add = """
  Map<String, dynamic> toStorageJson() => {
    'product': product == null ? null : {
      'id': product!.id, 'name': product!.name, 'category': product!.category,
      'subcategory_id': product!.subcategoryId, 'price': product!.price,
      'image_url': product!.imageUrl, 'images': product!.images,
      'description': product!.description, 'is_active': product!.isActive,
      'colors': product!.colors, 'brand': product!.brand, 'rating': product!.rating,
      'review_count': product!.reviewCount, 'stock_quantity': product!.stockQuantity,
      'is_new': product!.isNew, 'reward_points': product!.rewardPoints,
      'sales_count': product!.salesCount, 'allow_points_payment': product!.allowPointsPayment,
      'specifications': product!.specifications,
    },
    'color': color, 'inquiry_id': inquiryId, 'option_id': optionId,
    'image_url': imageUrl, 'inquiry_device_model': inquiryDeviceModel,
    'inquiry_price': inquiryPrice, 'quantity': quantity,
  };

  factory CartLine.fromStorageJson(Map<String, dynamic> data) {
    final rawProduct = data['product'];
    final Product? restoredProduct = rawProduct is Map
        ? Product.fromMap((rawProduct['id'] ?? '').toString(), Map<String, dynamic>.from(rawProduct))
        : null;
    return CartLine(
      product: restoredProduct,
      color: data['color']?.toString(),
      inquiryId: data['inquiry_id']?.toString(),
      optionId: data['option_id']?.toString(),
      imageUrl: data['image_url']?.toString(),
      inquiryDeviceModel: data['inquiry_device_model']?.toString(),
      inquiryPrice: (data['inquiry_price'] as num?)?.toDouble(),
      quantity: (data['quantity'] as num?)?.toInt() ?? 1,
    );
  }
"""
if "toStorageJson()" not in s:
    if line_anchor not in s:
        raise SystemExit("CartLine total getter anchor missing")
    s = s.replace(line_anchor, line_anchor + line_add, 1)

items_anchor = "  final List<CartLine> _items = [];\n"
storage_add = """
  static const String _storageKey = 'astro_mobile_cart_v1';

  Future<void> initialize() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(_storageKey);
      if (raw == null || raw.isEmpty) return;
      final decoded = jsonDecode(raw);
      if (decoded is! List) return;
      _items
        ..clear()
        ..addAll(decoded.whereType<Map>().map(
          (item) => CartLine.fromStorageJson(Map<String, dynamic>.from(item)),
        ));
      notifyListeners();
    } catch (e) {
      debugPrint('ASTRO cart restore failed: $e');
    }
  }

  Future<void> _persist() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_storageKey, jsonEncode(_items.map((item) => item.toStorageJson()).toList()));
    } catch (e) {
      debugPrint('ASTRO cart save failed: $e');
    }
  }
"""
if "_storageKey" not in s:
    if items_anchor not in s:
        raise SystemExit("CartService items anchor missing")
    s = s.replace(items_anchor, items_anchor + storage_add, 1)

head, tail = s.split("  List<CartLine> get items", 1)
tail = tail.replace("    notifyListeners();", "    _persist();\n    notifyListeners();")
s = head + "  List<CartLine> get items" + tail
cart_path.write_text(s, encoding="utf-8")

main_path = root / "lib/main.dart"
m = main_path.read_text(encoding="utf-8")
if "import 'services/cart_service.dart';" not in m:
    m = m.replace(
        "import 'services/notification_service.dart';",
        "import 'services/notification_service.dart';\nimport 'services/cart_service.dart';",
        1,
    )
if "await CartService.instance.initialize();" not in m:
    m = m.replace(
        "  WidgetsFlutterBinding.ensureInitialized();",
        "  WidgetsFlutterBinding.ensureInitialized();\n  await CartService.instance.initialize();",
        1,
    )
main_path.write_text(m, encoding="utf-8")

# Remove the complete success banner from the actual add-to-cart method.
detail_path = root / "lib/screens/product_detail_screen.dart"
d = detail_path.read_text(encoding="utf-8")
start_marker = "    CartService.instance.add(product, selectedColor, quantity: selectedQuantity);"
end_marker = "\n  }\n\n  void _changeImage(int delta)"
start = d.find(start_marker)
if start < 0:
    raise SystemExit("Product detail cart-add call was not found")
end = d.find(end_marker, start)
if end < 0:
    raise SystemExit("End of _addToCart method was not found")
d = d[:start] + start_marker + "\n" + d[end:]
d = d.replace("import 'cart_screen.dart';\n", "")
if "SnackBarAction(" in d or "تمت إضافة ${product.name} إلى السلة" in d:
    raise SystemExit("Product detail success snackbar remains after removal")
detail_path.write_text(d, encoding="utf-8")


# Restore the intended brief success toast: two seconds, an explicit X, and a cart action.
detail_import = "import 'cart_screen.dart';"
if detail_import not in d:
    d = d.replace("import '../services/cart_service.dart';", "import '../services/cart_service.dart';\n" + detail_import, 1)
detail_helper = """
  void _showCartAddedMessage(String productName) {
    final messenger = ScaffoldMessenger.of(context);
    messenger.hideCurrentSnackBar();
    messenger.showSnackBar(
      SnackBar(
        duration: const Duration(seconds: 2),
        behavior: SnackBarBehavior.floating,
        content: Row(
          children: [
            Expanded(child: Text('تمت إضافة $productName إلى السلة')),
            IconButton(
              tooltip: 'إغلاق',
              visualDensity: VisualDensity.compact,
              onPressed: () => messenger.hideCurrentSnackBar(),
              icon: const Icon(Icons.close, color: Colors.white, size: 20),
            ),
          ],
        ),
        action: SnackBarAction(
          label: 'عرض السلة',
          textColor: Colors.white,
          onPressed: () => Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const CartScreen()),
          ),
        ),
      ),
    );
  }

"""
if "_showCartAddedMessage(String productName)" not in d:
    d = d.replace("  void _addToCart() {", detail_helper + "  void _addToCart() {", 1)
d = d.replace(
    "    CartService.instance.add(product, selectedColor, quantity: selectedQuantity);\n",
    "    CartService.instance.add(product, selectedColor, quantity: selectedQuantity);\n    _showCartAddedMessage(product.name);\n",
    1,
)
detail_path.write_text(d, encoding="utf-8")

# Home quick-add uses the same two-second closeable toast and cart action.
home_path = root / "lib/screens/home_screen.dart"
home = home_path.read_text(encoding="utf-8")
home_helper = """
  void cartAddedMessage(String productName) {
    final messenger = ScaffoldMessenger.of(context);
    messenger.hideCurrentSnackBar();
    messenger.showSnackBar(
      SnackBar(
        duration: const Duration(seconds: 2),
        behavior: SnackBarBehavior.floating,
        content: Row(
          children: [
            Expanded(child: Text('تمت إضافة $productName إلى السلة')),
            IconButton(
              tooltip: 'إغلاق',
              visualDensity: VisualDensity.compact,
              onPressed: () => messenger.hideCurrentSnackBar(),
              icon: const Icon(Icons.close, color: Colors.white, size: 20),
            ),
          ],
        ),
        action: SnackBarAction(
          label: 'عرض السلة',
          textColor: Colors.white,
          onPressed: () => Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const CartScreen()),
          ),
        ),
      ),
    );
  }

"""
if "void cartAddedMessage(String productName)" not in home:
    home = home.replace("  void message(String value) {", home_helper + "  void message(String value) {", 1)
home = home.replace("message('تمت إضافة ${p.name} إلى السلة');", "cartAddedMessage(p.name);")
home_path.write_text(home, encoding="utf-8")

# Inquiry option success uses the same toast; duplicate-option warning remains unchanged.
inq_path = root / "lib/screens/product_inquiry_inline.dart"
inq = inq_path.read_text(encoding="utf-8")
if "import 'cart_screen.dart';" not in inq:
    inq = inq.replace("import '../services/cart_service.dart';", "import '../services/cart_service.dart';\nimport 'cart_screen.dart';", 1)
inq_helper = """
  void _cartAddedMessage(String productName) {
    if (!mounted) return;
    final messenger = ScaffoldMessenger.of(context);
    messenger.hideCurrentSnackBar();
    messenger.showSnackBar(
      SnackBar(
        duration: const Duration(seconds: 2),
        behavior: SnackBarBehavior.floating,
        content: Row(
          children: [
            Expanded(child: Text('تمت إضافة $productName إلى السلة')),
            IconButton(
              tooltip: 'إغلاق',
              visualDensity: VisualDensity.compact,
              onPressed: () => messenger.hideCurrentSnackBar(),
              icon: const Icon(Icons.close, color: Colors.white, size: 20),
            ),
          ],
        ),
        action: SnackBarAction(
          label: 'عرض السلة',
          textColor: Colors.white,
          onPressed: () => Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const CartScreen()),
          ),
        ),
      ),
    );
  }

"""
if "void _cartAddedMessage(String productName)" not in inq:
    inq = inq.replace("  void _message(String value) {", inq_helper + "  void _message(String value) {", 1)
inq = inq.replace(
    "_message(added ? 'تمت إضافة الخيار إلى السلة' : 'هذا الخيار موجود بالفعل في السلة');",
    "if (added) { _cartAddedMessage('الخيار'); } else { _message('هذا الخيار موجود بالفعل في السلة'); }",
)
inq_path.write_text(inq, encoding="utf-8")

# Assertions: all three add flows show a 2-second toast with a close control and cart action.
for path in [detail_path, home_path, inq_path]:
    text = path.read_text(encoding="utf-8")
    if "Duration(seconds: 2)" not in text or "عرض السلة" not in text or "Icons.close" not in text:
        raise SystemExit(f"Missing closeable two-second cart toast in {path}")
print("Persistent cart retained; product, quick-add and inquiry additions show a 2-second closeable toast with View Cart.")

