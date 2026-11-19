from pathlib import Path

TARGET = Path('astro_mobile/lib/services/product_repository.dart')
if not TARGET.is_file():
    raise SystemExit(f'Product repository not found: {TARGET}')

source = TARGET.read_text(encoding='utf-8')

old_categories = '''  static Stream<List<StoreCategory>> watchCategories() async* {
    final cached = await _readCachedCategories();
    if (cached != null) yield cached;

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
  }
'''

new_categories = '''  static Stream<List<StoreCategory>> watchCategories() async* {
    // Offline-first: render the last successful categories before networking.
    final cached = await _readCachedCategories();
    if (cached != null) yield cached;

    // A successful REST response confirms that the server catalogue is reachable.
    // Do not attach a realtime stream after a failed request: its initial empty
    // emission while offline can overwrite the valid local catalogue in the UI.
    try {
      final response = await _db.from('categories').select();
      final categories = List<Map<String, dynamic>>.from(response)
          .map(StoreCategory.fromMap)
          .where((category) => category.id > 0 && category.name.isNotEmpty)
          .toList()
        ..sort((a, b) => a.sortOrder.compareTo(b.sortOrder));
      await _saveCachedCategories(categories);
      yield categories;
    } catch (_) {
      if (cached == null) rethrow;
      return;
    }

    // Online: keep the local snapshot current as categories change.
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
  }
'''

if old_categories not in source:
    raise SystemExit('Expected watchCategories implementation not found; no changes made.')
source = source.replace(old_categories, new_categories, 1)

old_products_catch = '''    } catch (_) {
      // A temporary REST failure must not erase or replace the cached list.
      // Continue to the realtime subscription; the UI keeps the last data.
      if (cached == null) rethrow;
    }

    // 3) Subscribe to realtime changes and persist only successful snapshots.
'''
new_products_catch = '''    } catch (_) {
      // Keep the last successful local catalogue visible while offline.
      // Do not start realtime after a failed REST request: an offline/failed
      // initial realtime snapshot can emit [] and replace the cached UI list.
      if (cached == null) rethrow;
      return;
    }

    // 3) Only after a successful REST refresh, subscribe to online realtime
    // changes and persist each successful snapshot.
'''
if old_products_catch not in source:
    raise SystemExit('Expected watchProducts error handling not found; no changes made.')
source = source.replace(old_products_catch, new_products_catch, 1)

TARGET.write_text(source, encoding='utf-8')
print('Offline-first product and category cache patch applied.')
