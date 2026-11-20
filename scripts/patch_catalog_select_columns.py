from pathlib import Path

target = Path("astro_mobile/lib/services/product_repository.dart")
if not target.is_file():
    raise SystemExit(f"Missing source file: {target}")

source = target.read_text(encoding="utf-8")

replacements = [
    (
        "final response = await _db.from('categories').select();",
        "final response = await _db.from('categories').select('id,name,parent_id,sort_order,is_active,image_url');",
    ),
    (
        ".from('products')\n          .select()\n          .eq('is_active', true);",
        ".from('products')\n          .select('id,name,price,category,stock,description,image_url,is_active,colors,subcategory_id,reward_points,allow_points_payment')\n          .eq('is_active', true);",
    ),
]

for old, new in replacements:
    if old not in source:
        raise SystemExit(f"Expected query not found; refusing partial patch: {old!r}")
    source = source.replace(old, new, 1)

target.write_text(source, encoding="utf-8")
print("Catalogue REST queries now select only columns used by the app.")
