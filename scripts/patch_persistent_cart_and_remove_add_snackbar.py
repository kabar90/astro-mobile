from pathlib import Path
import re

root = Path("astro_mobile")

# Product detail: remove only the successful-add SnackBar, keeping validation errors.
p = root / "lib/screens/product_detail_screen.dart"
s = p.read_text(encoding="utf-8")
pattern = re.compile(
    r"(    CartService\.instance\.add\(product, selectedColor, quantity: selectedQuantity\);)\n"
    r"    ScaffoldMessenger\.of\(context\)\.showSnackBar\(\n"
    r"      SnackBar\(\n"
    r"        content: Text\('تمت إضافة \$\{product\.name\} إلى السلة'\),\n"
    r"        action: SnackBarAction\(.*?\n"
    r"      \),\n"
    r"    \);",
    re.S,
)
s, n = pattern.subn(r"\1", s, count=1)
if n == 0 and "تمت إضافة ${product.name} إلى السلة" in s:
    raise SystemExit("Could not safely remove product success SnackBar")
p.write_text(s, encoding="utf-8")

# Home quick-add: remove success toast call, leave other messages intact.
p = root / "lib/screens/home_screen.dart"
s = p.read_text(encoding="utf-8")
s = s.replace("                                message('تمت إضافة ${p.name} إلى السلة');\n", "")
p.write_text(s, encoding="utf-8")

# Inquiry option: do not show a bottom toast on successful add; retain duplicate warning.
p = root / "lib/screens/product_inquiry_inline.dart"
s = p.read_text(encoding="utf-8")
old = "_message(added ? 'تمت إضافة الخيار إلى السلة' : 'هذا الخيار موجود بالفعل في السلة');"
new = "if (!added) _message('هذا الخيار موجود بالفعل في السلة');"
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")

# Assert no success-to-cart banners remain in these flows.
detail = (root / "lib/screens/product_detail_screen.dart").read_text(encoding="utf-8")
home = (root / "lib/screens/home_screen.dart").read_text(encoding="utf-8")
inquiry = (root / "lib/screens/product_inquiry_inline.dart").read_text(encoding="utf-8")
if "تمت إضافة ${product.name} إلى السلة" in detail:
    raise SystemExit("Product detail success SnackBar still exists")
if "message('تمت إضافة ${p.name} إلى السلة')" in home:
    raise SystemExit("Home success SnackBar still exists")
if "_message(added ? 'تمت إضافة الخيار إلى السلة'" in inquiry:
    raise SystemExit("Inquiry success SnackBar still exists")

print("Removed bottom success SnackBars for product and inquiry cart additions.")
