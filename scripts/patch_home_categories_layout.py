from pathlib import Path

p = Path("astro_mobile/lib/screens/home_screen.dart")
s = p.read_text(encoding="utf-8")

# Fix the active category grid. The former cells were too short for the
# image, category title and subcategory badge, causing visible overflow.
old_grid = "childAspectRatio: displaySettings.mainLayout == 'grid_3' ? .88 : 1.12,"
new_grid = "childAspectRatio: displaySettings.mainLayout == 'grid_3' ? .66 : .95,"
if old_grid in s:
    s = s.replace(old_grid, new_grid, 1)
elif new_grid not in s:
    raise SystemExit("Category grid aspect ratio was not found")

# Increase vertical separation between category cards.
grid_marker = "childAspectRatio: displaySettings.mainLayout == 'grid_3' ? .66 : .95,"
pos = s.find(grid_marker)
if pos < 0:
    raise SystemExit("Updated category grid setting was not found")
prefix = s[:pos]
spacing_pos = prefix.rfind("mainAxisSpacing: 12,")
if spacing_pos >= 0 and pos - spacing_pos < 180:
    s = s[:spacing_pos] + "mainAxisSpacing: 18," + s[spacing_pos + len("mainAxisSpacing: 12,"):]

# Keep the horizontal category carousel safe as well, if this layout is selected.
s = s.replace(
    "height: 174,\n                child: ListView.separated(",
    "height: 196,\n                child: ListView.separated(",
    1,
)
# Add an Offers shortcut beside the database-driven main categories.
tile = """                    itemCount: homeCategoryTiles.length,
                    separatorBuilder: (_, __) => const SizedBox(width: 10),
                    itemBuilder: (context, index) {
                      final item = homeCategoryTiles[index];"""
tile_new = """                    itemCount: homeCategoryTiles.length + 1,
                    separatorBuilder: (_, __) => const SizedBox(width: 10),
                    itemBuilder: (context, index) {
                      if (index == homeCategoryTiles.length) {
                        return SizedBox(width: 164, child: Material(color: Colors.transparent, child: InkWell(
                          borderRadius: BorderRadius.circular(20),
                          onTap: () {
                            final target = _homeOffersSectionKey.currentContext;
                            if (target != null) Scrollable.ensureVisible(target, duration: const Duration(milliseconds: 450), curve: Curves.easeInOut, alignment: 0.08);
                          },
                          child: Ink(decoration: BoxDecoration(color: const Color(0xFFFFE1E8), borderRadius: BorderRadius.circular(20), border: Border.all(color: const Color(0xFFFFC8D2))), padding: const EdgeInsets.all(9), child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                            Expanded(child: Image.asset('assets/category_offers.jpg', fit: BoxFit.contain, errorBuilder: (_, __, ___) => const Icon(Icons.local_offer_rounded, color: Color(0xFFE44755), size: 48))),
                            const SizedBox(height: 6),
                            const Text('العروض', style: TextStyle(color: astroNavy, fontSize: 11, fontWeight: FontWeight.w900)),
                          ])),
                        )));
                      }
                      final item = homeCategoryTiles[index];"""
s = s.replace(tile, tile_new, 1)

# Increase the featured section's top and bottom padding. This is separate
# from the grid cell-height fix and prevents the heading from crowding the grid.
s = s.replace(
    "padding: const EdgeInsets.fromLTRB(18, 2, 18, 12),",
    "padding: const EdgeInsets.fromLTRB(18, 12, 18, 16),",
    1,
)

if "منتجات مختارة" not in s:
    raise SystemExit("Featured-products heading was not found")
if new_grid not in s or "mainAxisSpacing: 18" not in s:
    raise SystemExit("Category grid spacing verification failed")

p.write_text(s, encoding="utf-8")
print("Fixed category grid overflow and added spacing before featured products.")
