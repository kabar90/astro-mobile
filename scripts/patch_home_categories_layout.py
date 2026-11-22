from pathlib import Path
root = Path('astro_mobile')
p = root / 'lib/screens/home_screen.dart'
s = p.read_text(encoding='utf-8')
old = '''              child: SizedBox(
                height: 176,
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.symmetric(horizontal: 16),'''
new = '''              child: SizedBox(
                // Extra room prevents the category subtitle/count chip from
                // overflowing on devices with larger system font scaling.
                height: 196,
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),'''
if old not in s:
    raise SystemExit('Missing root category carousel layout anchor')
s = s.replace(old, new, 1)
old2 = '''              child: Padding(
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
              ),'''
new2 = '''              child: Padding(
                // Keep the featured-products heading clearly separated from
                // the category carousel above it.
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
              ),'''
if old2 not in s:
    raise SystemExit('Missing featured products heading anchor')
s = s.replace(old2, new2, 1)
p.write_text(s, encoding='utf-8')
print('Home category carousel spacing and featured heading alignment patched.')
