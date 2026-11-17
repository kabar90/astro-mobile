from pathlib import Path
import sys

root = Path(sys.argv[1])
home = root / "lib/screens/home_screen.dart"
repo = root / "lib/services/product_repository.dart"
h = home.read_text(encoding="utf-8")
r = repo.read_text(encoding="utf-8")

def once(src, old, new, label):
    count = src.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, got {count}")
    return src.replace(old, new, 1)

r = once(r, "  final bool isActive;\n\n  const StoreCategory({", "  final bool isActive;\n  final String imageUrl;\n\n  const StoreCategory({", "category image field")
r = once(r, "    required this.isActive,\n  });", "    required this.isActive,\n    this.imageUrl = '',\n  });", "category image constructor")
r = once(r, "      isActive: row['is_active'] is bool ? row['is_active'] as bool : true,\n    );", "      isActive: row['is_active'] is bool ? row['is_active'] as bool : true,\n      imageUrl: (row['image_url'] ?? '').toString().trim(),\n    );", "category image map")
settings_model = """
class StoreDisplaySettings {
  final String productLayout;
  final int gridColumns;
  final bool allowCustomerToggle;

  const StoreDisplaySettings({
    this.productLayout = 'grid',
    this.gridColumns = 2,
    this.allowCustomerToggle = true,
  });

  factory StoreDisplaySettings.fromMap(Map<String, dynamic> row) {
    final columns = int.tryParse('${row['grid_columns'] ?? 2}') ?? 2;
    return StoreDisplaySettings(
      productLayout: row['product_layout']?.toString() == 'list' ? 'list' : 'grid',
      gridColumns: columns == 3 ? 3 : 2,
      allowCustomerToggle: row['allow_customer_toggle'] != false,
    );
  }
}
"""
r = once(r, "\nclass ProductRepository {", "\n" + settings_model + "\nclass ProductRepository {", "settings model insertion")
r = once(r, "  static Stream<List<Product>> watchProducts() {", """  static Stream<StoreDisplaySettings> watchDisplaySettings() {
    return _db
        .from('store_display_settings')
        .stream(primaryKey: ['id'])
        .map((rows) => rows.isEmpty
            ? const StoreDisplaySettings()
            : StoreDisplaySettings.fromMap(rows.first));
  }

  static Stream<List<Product>> watchProducts() {""", "settings realtime stream")
repo.write_text(r, encoding="utf-8")

h = once(h, """                                    child: Image.asset(
                                      categoryAsset,
                                      fit: BoxFit.contain,
                                      errorBuilder: (_, __, ___) => Icon(
                                        _categoryIcon(item.name),
                                        color: astroBlue,
                                        size: 42,
                                      ),
                                    ),""", """                                    child: item.imageUrl.isNotEmpty
                                        ? Image.network(
                                            item.imageUrl,
                                            fit: BoxFit.contain,
                                            errorBuilder: (_, __, ___) => Image.asset(
                                              categoryAsset,
                                              fit: BoxFit.contain,
                                              errorBuilder: (_, __, ___) => Icon(_categoryIcon(item.name), color: astroBlue, size: 42),
                                            ),
                                          )
                                        : Image.asset(
                                            categoryAsset,
                                            fit: BoxFit.contain,
                                            errorBuilder: (_, __, ___) => Icon(_categoryIcon(item.name), color: astroBlue, size: 42),
                                          ),""", "home root category image")
h = once(h, """                                child: Image.asset(
                                  categoryAsset,
                                  fit: BoxFit.cover,
                                  errorBuilder: (_, __, ___) => Icon(
                                    categoryIcon,
                                    color: astroBlue,
                                    size: 34,
                                  ),
                                ),""", """                                child: item.imageUrl.isNotEmpty
                                    ? Image.network(
                                        item.imageUrl,
                                        fit: BoxFit.cover,
                                        errorBuilder: (_, __, ___) => Image.asset(
                                          categoryAsset,
                                          fit: BoxFit.cover,
                                          errorBuilder: (_, __, ___) => Icon(categoryIcon, color: astroBlue, size: 34),
                                        ),
                                      )
                                    : Image.asset(
                                        categoryAsset,
                                        fit: BoxFit.cover,
                                        errorBuilder: (_, __, ___) => Icon(categoryIcon, color: astroBlue, size: 34),
                                      ),""", "category page root image")
h = once(h, """                    if (showBrandLogo)
                      _phoneBrandLogo(name)
                    else if (photoAsset != null)""", """                    if (item.imageUrl.isNotEmpty)
                      Positioned.fill(
                        child: Padding(
                          padding: const EdgeInsets.all(8),
                          child: ClipRRect(
                            borderRadius: BorderRadius.circular(12),
                            child: Image.network(
                              item.imageUrl,
                              fit: BoxFit.contain,
                              errorBuilder: (_, __, ___) => showBrandLogo
                                  ? _phoneBrandLogo(name)
                                  : (photoAsset != null
                                      ? Image.asset(photoAsset, fit: BoxFit.contain)
                                      : Icon(_subcategoryIcon(name), color: astroBlue, size: 40)),
                            ),
                          ),
                        ),
                      )
                    else if (showBrandLogo)
                      _phoneBrandLogo(name)
                    else if (photoAsset != null)""", "subcategory custom image")

h = once(h, "  int? categoryPageRootId;\n  int? categoryPageSubcategoryId;", "  int? categoryPageRootId;\n  int? categoryPageSubcategoryId;\n  String? _categoryLayoutOverride;", "layout override state")
start = h.index("  Widget _buildCategoriesPage({")
end = h.index("\n  Widget _buildStorePage(", start)
section = h[start:end]
section = once(section, "    return CustomScrollView(\n      slivers: [", """    return StreamBuilder<StoreDisplaySettings>(
      stream: ProductRepository.watchDisplaySettings(),
      builder: (context, settingsSnapshot) {
        final settings = settingsSnapshot.data ?? const StoreDisplaySettings();
        final layout = _categoryLayoutOverride ?? settings.productLayout;
        final useList = layout == 'list';
        return CustomScrollView(
      slivers: [""", "wrap category page stream")
section = once(section, """                  Text(
                    '${visibleProducts.length} منتجات',
                    style: const TextStyle(
                        color: Colors.black45, fontSize: 12),
                  ),""", """                  if (settings.allowCustomerToggle)
                    IconButton(
                      tooltip: useList ? 'عرض شبكي' : 'عرض أفقي',
                      visualDensity: VisualDensity.compact,
                      onPressed: () => setState(() {
                        _categoryLayoutOverride = useList ? 'grid' : 'list';
                      }),
                      icon: Icon(useList ? Icons.grid_view_rounded : Icons.view_agenda_rounded, color: astroBlue),
                    ),
                  Text(
                    '${visibleProducts.length} منتجات',
                    style: const TextStyle(
                        color: Colors.black45, fontSize: 12),
                  ),""", "customer layout toggle")
section = once(section, """          else
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
              sliver: SliverGrid(
                delegate: SliverChildBuilderDelegate(
                  (context, index) => _product(visibleProducts[index]),
                  childCount: visibleProducts.length,
                ),
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  mainAxisSpacing: 14,
                  crossAxisSpacing: 14,
                  childAspectRatio: .72,
                ),
              ),
            ),""", """          else if (useList)
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
              sliver: SliverList(
                delegate: SliverChildBuilderDelegate(
                  (context, index) => Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: _productListTile(visibleProducts[index]),
                  ),
                  childCount: visibleProducts.length,
                ),
              ),
            )
          else
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
              sliver: SliverGrid(
                delegate: SliverChildBuilderDelegate(
                  (context, index) => _product(visibleProducts[index]),
                  childCount: visibleProducts.length,
                ),
                gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: settings.gridColumns,
                  mainAxisSpacing: 14,
                  crossAxisSpacing: 14,
                  childAspectRatio: settings.gridColumns == 3 ? .58 : .72,
                ),
              ),
            ),""", "grid/list rendering")
section = once(section, """        ],
      ],
    );
  }""", """        ],
      ],
        );
      },
    );
  }""", "close category settings stream")
h = h[:start] + section + h[end:]

list_tile = """  Widget _productListTile(Product p) {
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ProductDetailScreen(product: p))),
        child: Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(borderRadius: BorderRadius.circular(16), border: Border.all(color: const Color(0xFFE0EAF5))),
          child: Row(children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: SizedBox(
                width: 104, height: 104,
                child: p.imageUrl.isEmpty
                    ? _placeholder(p.category, false)
                    : Image.network(p.imageUrl, fit: BoxFit.contain, errorBuilder: (_, __, ___) => _placeholder(p.category, false)),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(p.name, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(color: astroNavy, fontWeight: FontWeight.w800, fontSize: 14)),
                  const SizedBox(height: 8),
                  Text('${p.price.toStringAsFixed(0)} د.ل', style: const TextStyle(color: astroBlue, fontSize: 14, fontWeight: FontWeight.w900)),
                ],
              ),
            ),
            const Icon(Icons.chevron_left_rounded, color: astroBlue),
          ]),
        ),
      ),
    );
  }

"""
h = once(h, "  Widget _buildStorePage(List<Product> products) {", list_tile + "  Widget _buildStorePage(List<Product> products) {", "horizontal product tile insertion")
home.write_text(h, encoding="utf-8")
print("Category controls applied successfully.")
