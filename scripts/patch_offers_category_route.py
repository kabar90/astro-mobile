from pathlib import Path

p = Path("astro_mobile/lib/screens/home_screen.dart")
s = p.read_text(encoding="utf-8")

old = """                          onTap: () => setState(() {
                            categoryPageRootId = item.id;
                            categoryPageSubcategoryId = null;
                          }),"""
new = """                          onTap: () {
                            if (item.name.contains('العروض') || item.name.contains('تخفيض')) {
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (_) => _AllOffersScreen(products: products),
                                ),
                              );
                              return;
                            }
                            setState(() {
                              categoryPageRootId = item.id;
                              categoryPageSubcategoryId = null;
                            });
                          },"""
if old in s:
    s = s.replace(old, new, 1)
elif "_AllOffersScreen(products: products)" not in s:
    raise SystemExit("Category tap handler anchor not found")

# Keep the complete category label visible and give the offers card a meaningful caption.
s = s.replace("                                  maxLines: 1,\n                                  overflow: TextOverflow.ellipsis,\n                                  textAlign: TextAlign.center,",
              "                                  maxLines: 2,\n                                  overflow: TextOverflow.ellipsis,\n                                  textAlign: TextAlign.center,", 1)
carousel_old = """                            onTap: () => setState(() {
                              category = item.name;
                              selectedCategoryId = item.id;
                              selectedSubcategoryId = null;
                              categoryPageRootId = item.id;
                              categoryPageSubcategoryId = null;
                              nav = 1;
                            }),"""
carousel_new = """                            onTap: () {
                              if (item.name.contains('العروض') || item.name.contains('تخفيض')) {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (_) => _AllOffersScreen(products: products),
                                  ),
                                );
                                return;
                              }
                              setState(() {
                                category = item.name;
                                selectedCategoryId = item.id;
                                selectedSubcategoryId = null;
                                categoryPageRootId = item.id;
                                categoryPageSubcategoryId = null;
                                nav = 1;
                              });
                            },"""
if carousel_old in s:
    s = s.replace(carousel_old, carousel_new, 1)
elif "category = item.name;" not in s:
    raise SystemExit("Home category carousel tap handler not found")

old_caption = """                                    childCount == 0
                                        ? 'تصفح المنتجات'
                                        : '$childCount أقسام فرعية',"""
new_caption = """                                    (item.name.contains('العروض') || item.name.contains('تخفيض'))
                                        ? 'تصفح العروض النشطة'
                                        : childCount == 0
                                            ? 'تصفح المنتجات'
                                            : '$childCount أقسام فرعية',"""
if old_caption in s:
    s = s.replace(old_caption, new_caption, 1)
elif "تصفح العروض النشطة" not in s:
    raise SystemExit("Category caption anchor not found")

p.write_text(s, encoding="utf-8")
print("Offers category now opens the complete active offers screen.")
