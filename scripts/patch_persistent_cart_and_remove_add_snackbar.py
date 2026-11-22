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

print("Persistent cart save/restore and complete removal of product success SnackBar applied.")
