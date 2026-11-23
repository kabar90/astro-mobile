from pathlib import Path

path = Path("astro_mobile/lib/screens/home_screen.dart")
source = path.read_text(encoding="utf-8")

old = """                                  Expanded(
                                    child: Image.asset(
                                      categoryAsset,
                                      fit: BoxFit.contain,
                                      errorBuilder: (_, __, ___) => Icon(
                                        _categoryIcon(item.name),
                                        color: astroBlue,
                                        size: 42,
                                      ),
                                    ),
                                  ),"""

new = """                                  Expanded(
                                    child: item.imageUrl.isNotEmpty
                                        ? AstroCachedImage(
                                            imageUrl: item.imageUrl,
                                            fit: BoxFit.contain,
                                            errorWidget: Image.asset(
                                              categoryAsset,
                                              fit: BoxFit.contain,
                                              errorBuilder: (_, __, ___) => Icon(
                                                _categoryIcon(item.name),
                                                color: astroBlue,
                                                size: 42,
                                              ),
                                            ),
                                          )
                                        : Image.asset(
                                            categoryAsset,
                                            fit: BoxFit.contain,
                                            errorBuilder: (_, __, ___) => Icon(
                                              _categoryIcon(item.name),
                                              color: astroBlue,
                                              size: 42,
                                            ),
                                          ),
                                  ),"""

# Scope the check to the home carousel. The same remote-image code also
# exists in the separate all-categories page, so a global check is unsafe.
carousel_start = source.find("itemCount: homeCategoryTiles.length")
if carousel_start < 0:
    raise SystemExit("Home category carousel marker was not found.")

carousel_end = source.find("SliverToBoxAdapter(", carousel_start + 1)
if carousel_end < 0:
    carousel_end = min(len(source), carousel_start + 12000)

carousel = source[carousel_start:carousel_end]
if "final item = homeCategoryTiles[index];" not in carousel:
    raise SystemExit("Could not verify the home category carousel block.")

if "child: item.imageUrl.isNotEmpty" in carousel and "imageUrl: item.imageUrl" in carousel:
    print("Verified: home category carousel already uses the database image_url.")
elif old in carousel:
    carousel = carousel.replace(old, new, 1)
    source = source[:carousel_start] + carousel + source[carousel_end:]
    path.write_text(source, encoding="utf-8")
    print("Patched home category carousel to use StoreCategory.imageUrl with local fallback.")
else:
    raise SystemExit("Exact home carousel image widget not found; no changes made.")

# Verify only the home carousel, not a matching widget elsewhere in the file.
check = path.read_text(encoding="utf-8")
start = check.find("itemCount: homeCategoryTiles.length")
end = check.find("SliverToBoxAdapter(", start + 1)
if end < 0:
    end = min(len(check), start + 12000)
home_block = check[start:end]
if "child: item.imageUrl.isNotEmpty" not in home_block or "imageUrl: item.imageUrl" not in home_block:
    raise SystemExit("Verification failed: home carousel is not bound to category.image_url.")
