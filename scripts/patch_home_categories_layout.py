from pathlib import Path
import re

p = Path("astro_mobile/lib/screens/home_screen.dart")
s = p.read_text(encoding="utf-8")

# The active three-column category grid was too short for each card's image,
# title and child-category badge. This caused badge overflow into the next sliver.
old_ratio = "childAspectRatio: displaySettings.mainLayout == 'grid_3' ? .88 : 1.12,"
new_ratio = "childAspectRatio: displaySettings.mainLayout == 'grid_3' ? .66 : .95,"
if old_ratio in s:
    s = s.replace(old_ratio, new_ratio, 1)
elif new_ratio not in s:
    raise SystemExit("Could not locate category grid aspect-ratio setting")

old_spacing = """                  mainAxisSpacing: 12,
                  crossAxisSpacing: 12,
                  childAspectRatio: displaySettings.mainLayout == 'grid_3' ? .66 : .95,"""
new_spacing = """                  mainAxisSpacing: 18,
                  crossAxisSpacing: 12,
                  childAspectRatio: displaySettings.mainLayout == 'grid_3' ? .66 : .95,"""
if old_spacing in s:
    s = s.replace(old_spacing, new_spacing, 1)

# Preserve the already-applied horizontal carousel adjustment when that layout is selected.
pattern = re.compile(
    r"(SliverToBoxAdapter\\s*\\(\\s*child:\\s*SizedBox\\s*\\(\\s*)"
    r"height:\\s*174,"
    r"(\\s*child:\\s*ListView\\.separated\\s*\\(\\s*"
    r"scrollDirection:\\s*Axis\\.horizontal,\\s*"
    r"padding:\\s*const EdgeInsets\\.symmetric\\(horizontal:\\s*16,\\s*vertical:\\s*4\\),\\s*"
    r"itemCount:\\s*rootCategories\\.length,)"
)
s, _ = pattern.subn(r"\\1height: 196,\\2", s, count=1)

# Give the featured-products heading its own breathing room after the grid.
old_heading = """              child: Padding(
                padding: const EdgeInsets.fromLTRB(18, 2, 18, 12),
                child: Row(
                  children: [
                    const Expanded(
                      child: Text(
                        'منتجات مختارة',
                        style: TextStyle(color: astroNavy, fontSize: 18, fontWeight: FontWeight.w900),
                      ),
                    ),
                    Text('${products.length} منتج', style: const TextStyle(color: Colors.black45, fontSize: 12)),
                  ],
                ),
              ),"""
new_heading = """              child: Padding(
                padding: const EdgeInsets.fromLTRB(18, 12, 18, 16),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    const Expanded(
                      child: Text(
                        'منتجات مختارة',
                        textAlign: TextAlign.right,
                        style: TextStyle(color: astroNavy, fontSize: 18, fontWeight: FontWeight.w900),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Text(
                      '${products.length} منتج',
                      textAlign: TextAlign.left,
                      style: const TextStyle(color: Colors.black54, fontSize: 12),
                    ),
                  ],
                ),
              ),"""
if old_heading in s:
    s = s.replace(old_heading, new_heading, 1)
elif "'منتجات مختارة'" not in s:
    raise SystemExit("Featured products heading not found")

p.write_text(s, encoding="utf-8")
print("Category grid cell height fixed; badges now fit inside cards and featured section has breathing room.")
