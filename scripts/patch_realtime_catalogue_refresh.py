from pathlib import Path

target = Path("astro_mobile/lib/services/product_repository.dart")
source = target.read_text(encoding="utf-8")

if "import 'dart:async';" not in source:
    source = source.replace("import 'dart:convert';", "import 'dart:async';\nimport 'dart:convert';", 1)

old_products = """    // 3) Only after a successful REST refresh, subscribe to online realtime
    // changes and persist each successful snapshot.
    yield* _db
        .from('products')
        .stream(primaryKey: ['id'])
        .eq('is_active', true)
        .asyncMap((rows) async {
          final products = _productsFromRows(rows);
          await _saveCachedProducts(products);
          return products;
        });
"""
new_products = """    // 3) Listen for product table changes without requesting a second
    // initial full-table snapshot. Refresh the narrow REST catalogue only
    // when an actual insert/update/delete event arrives.
    final changes = StreamController<List<Product>>();
    final channel = _db
        .channel('astro-products-catalogue')
        .onPostgresChanges(
          event: PostgresChangeEvent.all,
          schema: 'public',
          table: 'products',
          callback: (_) async {
            try {
              final updatedRows = await _db
                  .from('products')
                  .select('id,name,price,category,stock,image_url,is_active,colors,subcategory_id,reward_points,allow_points_payment')
                  .eq('is_active', true);
              final updated = _productsFromRows(
                List<Map<String, dynamic>>.from(updatedRows),
              );
              await _saveCachedProducts(updated);
              if (!changes.isClosed) changes.add(updated);
            } catch (_) {
              // Keep the last good catalogue if a background refresh fails.
            }
          },
        )
        .subscribe();

    try {
      yield* changes.stream;
    } finally {
      await _db.removeChannel(channel);
      await changes.close();
    }
"""
if source.count(old_products) != 1:
    raise SystemExit("Expected products realtime stream block not found exactly once; no patch applied.")
source = source.replace(old_products, new_products, 1)

old_categories = """    // Online: keep the local snapshot current as categories change.
    yield* _db
        .from('categories')
        .stream(primaryKey: ['id'])
        .asyncMap((rows) async {
          final categories = rows
              .map(StoreCategory.fromMap)
              .where((category) => category.id > 0 && category.name.isNotEmpty)
              .toList()
            ..sort((a, b) => a.sortOrder.compareTo(b.sortOrder));
          await _saveCachedCategories(categories);
          return categories;
        });
"""
new_categories = """    // Listen for category changes without a second initial table snapshot.
    final changes = StreamController<List<StoreCategory>>();
    final channel = _db
        .channel('astro-categories-catalogue')
        .onPostgresChanges(
          event: PostgresChangeEvent.all,
          schema: 'public',
          table: 'categories',
          callback: (_) async {
            try {
              final updatedRows = await _db
                  .from('categories')
                  .select('id,name,parent_id,sort_order,is_active,image_url');
              final updated = List<Map<String, dynamic>>.from(updatedRows)
                  .map(StoreCategory.fromMap)
                  .where((category) => category.id > 0 && category.name.isNotEmpty)
                  .toList()
                ..sort((a, b) => a.sortOrder.compareTo(b.sortOrder));
              await _saveCachedCategories(updated);
              if (!changes.isClosed) changes.add(updated);
            } catch (_) {
              // Keep the last good category list if a background refresh fails.
            }
          },
        )
        .subscribe();

    try {
      yield* changes.stream;
    } finally {
      await _db.removeChannel(channel);
      await changes.close();
    }
"""
if source.count(old_categories) != 1:
    raise SystemExit("Expected categories realtime stream block not found exactly once; no patch applied.")
source = source.replace(old_categories, new_categories, 1)

target.write_text(source, encoding="utf-8")
print("Replaced duplicate initial Realtime snapshots with change-triggered narrow REST refreshes.")
