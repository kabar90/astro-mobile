from pathlib import Path

path = Path('astro_mobile/lib/screens/home_screen.dart')
s = path.read_text()

old_sig = """    required String meta,
    required String actionLabel,
    required VoidCallback onTap,
"""
new_sig = """    required String meta,
    double? originalTotal,
    double? bundlePrice,
    required String actionLabel,
    required VoidCallback onTap,
"""
if s.count(old_sig) != 1:
    raise SystemExit(f'Expected one home card signature, found {s.count(old_sig)}')
s = s.replace(old_sig, new_sig, 1)

old_meta = """            SizedBox(
              height: 22,
              child: Center(
                child: Text(
                  meta,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(color: Color(0xFFE44755), fontSize: 12, fontWeight: FontWeight.w900),
                ),
              ),
            ),
"""
new_meta = """            SizedBox(
              height: 22,
              child: originalTotal != null && bundlePrice != null
                  ? FittedBox(
                      fit: BoxFit.scaleDown,
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(
                            '\${originalTotal.toStringAsFixed(2)} د.ل',
                            style: const TextStyle(
                              color: Color(0xFF9CAAC8),
                              fontSize: 10,
                              fontWeight: FontWeight.w800,
                              decoration: TextDecoration.lineThrough,
                            ),
                          ),
                          const SizedBox(width: 7),
                          Text(
                            '\${bundlePrice.toStringAsFixed(2)} د.ل',
                            style: const TextStyle(color: Color(0xFFE44755), fontSize: 12, fontWeight: FontWeight.w900),
                          ),
                        ],
                      ),
                    )
                  : Center(
                      child: Text(
                        meta,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(color: Color(0xFFE44755), fontSize: 12, fontWeight: FontWeight.w900),
                      ),
                    ),
            ),
"""
if s.count(old_meta) != 1:
    raise SystemExit(f'Expected one home card meta block, found {s.count(old_meta)}')
s = s.replace(old_meta, new_meta, 1)

old_bundle = """                              final bundlePrice = double.tryParse('\${offer['bundle_price'] ?? ''}') ?? 0;
                              final bundleProducts = bundleEntries.map((entry) => entry['product'] as Product).toList();
"""
new_bundle = """                              final bundlePrice = double.tryParse('\${offer['bundle_price'] ?? ''}') ?? 0;
                              final originalBundleTotal = bundleEntries.fold<double>(0, (sum, entry) {
                                final product = entry['product'] as Product;
                                final quantity = entry['quantity'] as int;
                                return sum + (product.price * quantity);
                              });
                              final bundleProducts = bundleEntries.map((entry) => entry['product'] as Product).toList();
"""
if s.count(old_bundle) != 1:
    raise SystemExit(f'Expected one bundle price calculation, found {s.count(old_bundle)}')
s = s.replace(old_bundle, new_bundle, 1)

old_call = """                                  meta: '\${bundlePrice.toStringAsFixed(2)} د.ل',
                                  actionLabel: 'تصفح الباقة',
"""
new_call = """                                  meta: '\${bundlePrice.toStringAsFixed(2)} د.ل',
                                  originalTotal: originalBundleTotal,
                                  bundlePrice: bundlePrice,
                                  actionLabel: 'تصفح الباقة',
"""
if s.count(old_call) != 1:
    raise SystemExit(f'Expected one featured bundle card call, found {s.count(old_call)}')
s = s.replace(old_call, new_call, 1)

old_product_map = """                                        return <String, dynamic>{'name': p.name, 'imageUrl': p.imageUrl, 'description': p.description};
"""
new_product_map = """                                        return <String, dynamic>{
                                          'name': p.name,
                                          'imageUrl': p.imageUrl,
                                          'description': p.description,
                                          'price': p.price,
                                          'quantity': entry['quantity'],
                                        };
"""
if s.count(old_product_map) != 1:
    raise SystemExit(f'Expected one bundle details product map, found {s.count(old_product_map)}')
s = s.replace(old_product_map, new_product_map, 1)

path.write_text(s)
print('Homepage bundle original-price display and details price/quantity binding applied.')
