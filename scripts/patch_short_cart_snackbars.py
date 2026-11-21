from pathlib import Path

ROOT = Path("astro_mobile")

def replace_once(path, old, new):
    file = ROOT / path
    source = file.read_text(encoding="utf-8")
    if old not in source:
        if new.strip() in source:
            return
        raise SystemExit(f"Patch anchor not found: {path}")
    file.write_text(source.replace(old, new, 1), encoding="utf-8")

replace_once(
    "lib/screens/home_screen.dart",
    """  void message(String value) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(value),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }""",
    """  void message(String value) {
    final messenger = ScaffoldMessenger.of(context);
    messenger.hideCurrentSnackBar();
    messenger.showSnackBar(
      SnackBar(
        content: Text(value),
        behavior: SnackBarBehavior.floating,
        duration: const Duration(seconds: 2),
      ),
    );
  }"""
)

replace_once(
    "lib/screens/product_detail_screen.dart",
    """    CartService.instance.add(product, selectedColor, quantity: selectedQuantity);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('تمت إضافة ${product.name} إلى السلة'),
        action: SnackBarAction("""
    ,
    """    CartService.instance.add(product, selectedColor, quantity: selectedQuantity);
    final messenger = ScaffoldMessenger.of(context);
    messenger.hideCurrentSnackBar();
    messenger.showSnackBar(
      SnackBar(
        duration: const Duration(seconds: 2),
        content: Text('تمت إضافة ${product.name} إلى السلة'),
        action: SnackBarAction("""
)

replace_once(
    "lib/screens/product_inquiry_inline.dart",
    """  void _message(String value) {
    if (mounted) ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(value), behavior: SnackBarBehavior.floating),
    );
  }""",
    """  void _message(String value) {
    if (!mounted) return;
    final messenger = ScaffoldMessenger.of(context);
    messenger.hideCurrentSnackBar();
    messenger.showSnackBar(
      SnackBar(
        content: Text(value),
        behavior: SnackBarBehavior.floating,
        duration: const Duration(seconds: 2),
      ),
    );
  }"""
)

print("Short, non-blocking cart confirmation messages applied.")
