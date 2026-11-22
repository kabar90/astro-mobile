from pathlib import Path
import re

p = Path("astro_mobile/lib/screens/home_screen.dart")
s = p.read_text(encoding="utf-8")

# Target only the root-category carousel (identified by rootCategories),
# not other horizontal lists in the home screen.
pattern = re.compile(
    r"(SliverToBoxAdapter\s*\(\s*child:\s*SizedBox\s*\(\s*)"
    r"height:\s*174,"
    r"(\s*child:\s*ListView\.separated\s*\(\s*"
    r"scrollDirection:\s*Axis\.horizontal,\s*"
    r"padding:\s*const EdgeInsets\.symmetric\(horizontal:\s*16,\s*vertical:\s*4\),\s*"
    r"itemCount:\s*rootCategories\.length,)"
)
s, count = pattern.subn(
    r"\1height: 196,\2",
    s,
    count=1,
)
if count != 1:
    raise SystemExit("Could not uniquely locate rootCategories carousel for spacing fix")

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
                padding: const EdgeInsets.fromLTRB(18, 8, 18, 14),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    Expanded(
                      child: Align(
                        alignment: Alignment.centerRight,
                        child: Text(
                          'منتجات مختارة',
                          textAlign: TextAlign.right,
                          style: const TextStyle(color: astroNavy, fontSize: 18, fontWeight: FontWeight.w900),
                        ),
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
if old_heading not in s:
    raise SystemExit("Could not locate featured-products heading block")
s = s.replace(old_heading, new_heading, 1)

p.write_text(s, encoding="utf-8")
print("Root-category carousel spacing and featured-products heading alignment applied.")
