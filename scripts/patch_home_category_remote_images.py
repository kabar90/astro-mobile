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

if new in source:
    print("Home category carousel already uses the database image_url.")
elif old in source:
    source = source.replace(old, new, 1)
    path.write_text(source, encoding="utf-8")
    print("Patched home category carousel to use StoreCategory.imageUrl with local fallback.")
else:
    raise SystemExit("Could not safely locate the exact home category image widget; no changes made.")

check = path.read_text(encoding="utf-8")
if "child: item.imageUrl.isNotEmpty" not in check or "AstroCachedImage(" not in check:
    raise SystemExit("Verification failed: remote category image widget is missing.")
