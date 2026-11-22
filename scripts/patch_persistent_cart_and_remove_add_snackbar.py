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

source = source[:start] + start_marker + "\n" + source[end:]
source = source.replace("import 'cart_screen.dart';\n", "")
if "SnackBarAction(" in source or "تمت إضافة ${product.name} إلى السلة" in source:
    raise SystemExit("Product detail success snackbar remains after removal")
detail_path.write_text(source, encoding="utf-8")

# The home screen's message helper has no call sites in the extracted source.
print("Removed the product-detail add-success SnackBar completely.")
