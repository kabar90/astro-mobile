from pathlib import Path

root = Path("astro_mobile")
detail_path = root / "lib/screens/product_detail_screen.dart"
source = detail_path.read_text(encoding="utf-8")

start_marker = "    CartService.instance.add(product, selectedColor, quantity: selectedQuantity);"
end_marker = "\n  }\n\n  void _changeImage(int delta)"
start = source.find(start_marker)
if start < 0:
    raise SystemExit("Product detail cart-add call was not found")
end = source.find(end_marker, start)
if end < 0:
    raise SystemExit("End of _addToCart method was not found")

replacement = start_marker + "\n"
source = source[:start] + replacement + source[end:]
source = source.replace("import 'cart_screen.dart';\n", "")
if "SnackBarAction(" in source or "تمت إضافة ${product.name} إلى السلة" in source:
    raise SystemExit("Product detail success snackbar remains after removal")
detail_path.write_text(source, encoding="utf-8")

# The home helper is unused by the quick-add UI; ensure no success call is attached to it.
home_path = root / "lib/screens/home_screen.dart"
home = home_path.read_text(encoding="utf-8")
if "message('تمت إضافة" in home:
    raise SystemExit("Unexpected home add-success notification call found")
print("Removed the product-detail add-success SnackBar completely.")
