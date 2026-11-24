from pathlib import Path

p = Path("astro_mobile/lib/screens/home_screen.dart")
s = p.read_text(encoding="utf-8")

field = "  static List<Product> _cachedHomeProducts = [];\n"
field_new = field + "  List<Widget> _allActiveOfferWidgets = [];\n"
if field in s:
    s = s.replace(field, field_new, 1)
elif "List<Widget> _allActiveOfferWidgets = [];" not in s:
    raise SystemExit("Offer widget state anchor not found")

anchor = "                        return Column("
assign = "                        _allActiveOfferWidgets = List<Widget>.unmodifiable(offerSections);\n" + anchor
if anchor in s:
    s = s.replace(anchor, assign, 1)
elif "_allActiveOfferWidgets = List<Widget>.unmodifiable(offerSections);" not in s:
    raise SystemExit("Offer list assignment anchor not found")

old = """                          onTap: () => setState(() {
                            categoryPageRootId = item.id;
                            categoryPageSubcategoryId = null;
                          }),"""
new = """                          onTap: () {
                            if (item.name.contains('العروض') || item.name.contains('تخفيض')) {
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (_) => _AllOffersScreen(offers: _allActiveOfferWidgets),
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
elif "offers: _allActiveOfferWidgets" not in s:
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
                                    builder: (_) => _AllOffersScreen(offers: _allActiveOfferWidgets),
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
