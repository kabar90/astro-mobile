from pathlib import Path

repo = Path("astro_mobile/lib/services/product_repository.dart")
screen = Path("astro_mobile/lib/screens/product_detail_screen.dart")

if not repo.is_file() or not screen.is_file():
    raise SystemExit("Required Flutter source files are missing; refusing to patch.")

r = repo.read_text(encoding="utf-8")
s = screen.read_text(encoding="utf-8")

old_select = ".select('id,name,price,category,stock,description,image_url,is_active,colors,subcategory_id,reward_points,allow_points_payment')"
new_select = ".select('id,name,price,category,stock,image_url,is_active,colors,subcategory_id,reward_points,allow_points_payment')"
if r.count(old_select) != 1:
    raise SystemExit("Expected catalogue select was not found exactly once; refusing patch.")
r = r.replace(old_select, new_select, 1)

anchor = "  static List<Product> _productsFromRows(List<Map<String, dynamic>> rows) {"
method = """  // Load the long-form description only when a customer opens product details.
  // Keep a separate persistent cache so offline product details remain available.
  static Future<String> getProductDescription(
    String productId, {
    String fallback = '',
  }) async {
    final key = 'astro_product_description_v1_$productId';
    try {
      final prefs = await SharedPreferences.getInstance();
      final cached = prefs.getString(key);
      if (cached != null && cached.trim().isNotEmpty) return cached;
      if (fallback.trim().isNotEmpty) {
        await prefs.setString(key, fallback);
        return fallback;
      }
      final row = await _db
          .from('products')
          .select('description')
          .eq('id', productId)
          .maybeSingle();
      final description = (row?['description'] ?? '').toString();
      if (description.isNotEmpty) await prefs.setString(key, description);
      return description;
    } catch (_) {
      return fallback;
    }
  }

"""
if r.count(anchor) != 1:
    raise SystemExit("Repository insertion point not found exactly once; refusing patch.")
r = r.replace(anchor, method + anchor, 1)

import_anchor = "import '../services/cart_service.dart';"
if s.count(import_anchor) != 1:
    raise SystemExit("Detail screen import anchor not found exactly once.")
s = s.replace(import_anchor, import_anchor + "\nimport '../services/product_repository.dart';", 1)

state_anchor = "  bool isFavorite = false;"
if s.count(state_anchor) != 1:
    raise SystemExit("Detail screen state anchor not found exactly once.")
s = s.replace(state_anchor, state_anchor + "\n  late String _productDescription;\n  bool _descriptionLoading = false;", 1)

init_anchor = "    super.initState();\n    if (widget.product.colors.length == 1) {"
if s.count(init_anchor) != 1:
    raise SystemExit("Detail screen initState anchor not found exactly once.")
s = s.replace(init_anchor, "    super.initState();\n    _productDescription = widget.product.description;\n    if (_productDescription.trim().isEmpty) _loadProductDescription();\n    if (widget.product.colors.length == 1) {", 1)

method_anchor = "  Color colorValue(String name) {"
loader = """  Future<void> _loadProductDescription() async {
    if (_descriptionLoading) return;
    _descriptionLoading = true;
    final description = await ProductRepository.getProductDescription(
      widget.product.id,
      fallback: _productDescription,
    );
    if (!mounted) return;
    setState(() {
      _productDescription = description;
      _descriptionLoading = false;
    });
  }

"""
if s.count(method_anchor) != 1:
    raise SystemExit("Detail screen method insertion point not found exactly once.")
s = s.replace(method_anchor, loader + method_anchor, 1)

old_text = """          Text(
            product.description.trim().isEmpty
                ? 'لا يوجد وصف متاح لهذا المنتج حالياً.'
                : product.description,
            textAlign: TextAlign.start,
            style: const TextStyle(
              color: Color(0xFF65758B),
              fontSize: 14,
              height: 1.8,
            ),
          ),"""
new_text = """          Text(
            _productDescription.trim().isEmpty
                ? (_descriptionLoading
                    ? 'جارٍ تحميل وصف المنتج...'
                    : 'لا يوجد وصف متاح لهذا المنتج حالياً.')
                : _productDescription,
            textAlign: TextAlign.start,
            style: const TextStyle(
              color: Color(0xFF65758B),
              fontSize: 14,
              height: 1.8,
            ),
          ),"""
if s.count(old_text) != 1:
    raise SystemExit("Description widget not found exactly once; refusing patch.")
s = s.replace(old_text, new_text, 1)

repo.write_text(r, encoding="utf-8")
screen.write_text(s, encoding="utf-8")
print("Applied lazy product-description loading with persistent offline detail cache.")
