from pathlib import Path
import re

root = Path("astro_mobile")
cart = root / "lib/services/cart_service.dart"
s = cart.read_text(encoding="utf-8")

if "shared_preferences/shared_preferences.dart" not in s:
    s = s.replace("import 'package:flutter/foundation.dart';",
                  "import 'dart:convert';\nimport 'package:flutter/foundation.dart';\nimport 'package:shared_preferences/shared_preferences.dart';", 1)

anchor = "  Map<String, dynamic> toOrderJson() {"
storage = """  Map<String, dynamic> toStorageJson() => {
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
    final product = rawProduct is Map
        ? Product.fromMap((rawProduct['id'] ?? '').toString(), Map<String, dynamic>.from(rawProduct))
        : null;
    return CartLine(
      product: product,
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
    if anchor not in s: raise SystemExit("CartLine serialization anchor missing")
    s = s.replace(anchor, storage + anchor, 1)

anchor = "  final List<CartLine> _items = [];"
init = """  final List<CartLine> _items = [];
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
      await prefs.setString(
        _storageKey,
        jsonEncode(_items.map((item) => item.toStorageJson()).toList()),
      );
    } catch (e) {
      debugPrint('ASTRO cart save failed: $e');
    }
  }
"""
if "_storageKey" not in s:
    if anchor not in s: raise SystemExit("Cart storage anchor missing")
    s = s.replace(anchor, init, 1)

# Persist after every cart mutation.
s = s.replace("    notifyListeners();", "    _persist();\n    notifyListeners();")
# Restore method's notify should not write an empty/intermediate state.
s = s.replace("      _persist();\n    notifyListeners();\n    } catch (e)", "      notifyListeners();\n    } catch (e)")
cart.write_text(s, encoding="utf-8")

main = root / "lib/main.dart"
m = main.read_text(encoding="utf-8")
if "services/cart_service.dart" not in m:
    m = m.replace("import 'services/notification_service.dart';",
                  "import 'services/notification_service.dart';\nimport 'services/cart_service.dart';", 1)
if "await CartService.instance.initialize();" not in m:
    m = m.replace("  WidgetsFlutterBinding.ensureInitialized();",
                  "  WidgetsFlutterBinding.ensureInitialized();\n  await CartService.instance.initialize();", 1)
main.write_text(m, encoding="utf-8")

# Remove the blocking add-to-cart snackbar (including its persistent action button).
detail = root / "lib/screens/product_detail_screen.dart"
d = detail.read_text(encoding="utf-8")
pattern = re.compile(r"    CartService\.instance\.add\(product, selectedColor, quantity: selectedQuantity\);\s*ScaffoldMessenger\.of\(context\)\.showSnackBar\(\s*SnackBar\(.*?\n    \);", re.S)
d2, n = pattern.subn("    CartService.instance.add(product, selectedColor, quantity: selectedQuantity);", d, count=1)
if n == 0 and "CartService.instance.add(product, selectedColor, quantity: selectedQuantity);" not in d:
    raise SystemExit("Product detail add-to-cart block not found")
detail.write_text(d2, encoding="utf-8")

home = root / "lib/screens/home_screen.dart"
h = home.read_text(encoding="utf-8")
h = h.replace("                                message('تمت إضافة ${p.name} إلى السلة');", "")
home.write_text(h, encoding="utf-8")

inquiry = root / "lib/screens/product_inquiry_inline.dart"
q = inquiry.read_text(encoding="utf-8")
q = q.replace("                              _message(added ? 'تمت إضافة الخيار إلى السلة' : 'هذا الخيار موجود بالفعل في السلة');",
              "                              if (!added) _message('هذا الخيار موجود بالفعل في السلة');")
inquiry.write_text(q, encoding="utf-8")

print("Persistent cart restore/save and non-blocking add-to-cart UX patch applied.")
