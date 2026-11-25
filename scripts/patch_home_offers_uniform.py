from pathlib import Path

home = Path('astro_mobile/lib/screens/home_screen.dart')
s = home.read_text(encoding='utf-8')

marker = '  int nav = 0;'
helper = r"""
  Widget _homeOfferPreviewCard({
    required BuildContext context,
    required String title,
    required String imageUrl,
    required String fallbackImageUrl,
    required String meta,
    required String actionLabel,
    required VoidCallback onTap,
  }) {
    return SizedBox(
      width: 174,
      height: 258,
      child: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: astroSurface,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: const Color(0xFFB45CFF), width: 1.2),
          boxShadow: const [
            BoxShadow(color: Color(0x221765C5), blurRadius: 10, offset: Offset(0, 3)),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: SizedBox(
                height: 112,
                child: imageUrl.trim().isEmpty && fallbackImageUrl.trim().isEmpty
                    ? const ColoredBox(
                        color: astroSurfaceAlt,
                        child: Center(child: Icon(Icons.local_offer_rounded, size: 38, color: Color(0xFF1765C5))),
                      )
                    : AstroCachedImage(
                        imageUrl: imageUrl.trim().isEmpty ? fallbackImageUrl : imageUrl,
                        fit: BoxFit.contain,
                        placeholder: const ColoredBox(
                          color: astroSurfaceAlt,
                          child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
                        ),
                        errorWidget: fallbackImageUrl.trim().isEmpty || fallbackImageUrl.trim() == imageUrl.trim()
                            ? const ColoredBox(
                                color: astroSurfaceAlt,
                                child: Center(child: Icon(Icons.local_offer_rounded, size: 38, color: Color(0xFF1765C5))),
                              )
                            : AstroCachedImage(
                                imageUrl: fallbackImageUrl,
                                fit: BoxFit.contain,
                                errorWidget: const ColoredBox(
                                  color: astroSurfaceAlt,
                                  child: Center(child: Icon(Icons.local_offer_rounded, size: 38, color: Color(0xFF1765C5))),
                                ),
                              ),
                      ),
              ),
            ),
            const SizedBox(height: 8),
            SizedBox(
              height: 40,
              child: Align(
                alignment: Alignment.center,
                child: Text(
                  title,
                  maxLines: 2,
                  textAlign: TextAlign.center,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(color: astroNavy, fontSize: 13, height: 1.15, fontWeight: FontWeight.w900),
                ),
              ),
            ),
            const SizedBox(height: 4),
            SizedBox(
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
            const Spacer(),
            SizedBox(
              height: 34,
              child: ElevatedButton(
                onPressed: onTap,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF1765C5),
                  foregroundColor: Colors.white,
                  elevation: 0,
                  padding: const EdgeInsets.symmetric(horizontal: 6),
                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
                child: Text(
                  actionLabel,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w800),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

"""
if '_homeOfferPreviewCard({' not in s:
    if marker not in s:
        raise SystemExit('Could not find HomeScreenState insertion point')
    s = s.replace(marker, helper + marker, 1)

old_bundle = "if (offer['show_on_home'] == true) featuredOfferSections.add(offerSections.last);"
bundle = """if (offer['show_on_home'] == true) {
                                featuredOfferSections.add(_homeOfferPreviewCard(
                                  context: context,
                                  title: offerName,
                                  imageUrl: (offer['cover_image_url'] ?? '').toString(),
                                  fallbackImageUrl: bundleEntries.isNotEmpty
                                      ? ((bundleEntries.first['product'] as Product).imageUrl)
                                      : '',
                                  meta: '${bundlePrice.toStringAsFixed(2)} د.ل',
                                  actionLabel: 'تصفح الباقة',
                                  onTap: () {
                                    final id = int.tryParse('${offer['id']}');
                                    if (id == null) return;
                                    Navigator.push(context, MaterialPageRoute(builder: (_) => BundleDetailsScreen(
                                      offerId: id,
                                      offerName: offerName,
                                      bundlePrice: bundlePrice,
                                      products: bundleEntries.map((entry) {
                                        final p = entry['product'] as Product;
                                        return <String, dynamic>{'name': p.name, 'imageUrl': p.imageUrl, 'description': p.description};
                                      }).toList(),
                                    )));
                                  },
                                ));
                              }"""
if old_bundle not in s:
    raise SystemExit('Bundle featured-card anchor not found')
s = s.replace(old_bundle, bundle, 1)

product = """if (offer['show_on_home'] == true) {
                                final firstProduct = usedProducts.isNotEmpty
                                    ? _findProduct(products, usedProducts.first)
                                    : null;
                                final cover = (offer['cover_image_url'] ?? '').toString().trim();
                                featuredOfferSections.add(_homeOfferPreviewCard(
                                  context: context,
                                  title: offerName,
                                  imageUrl: cover,
                                  fallbackImageUrl: firstProduct?.imageUrl ?? '',
                                  meta: '${offerCards.length} منتجات',
                                  actionLabel: 'تصفح العرض',
                                  onTap: () => Navigator.push(context, MaterialPageRoute(
                                    builder: (_) => _OfferProductsGridScreen(title: offerName, products: offerCards),
                                  )),
                                ));
                              }"""
if old_bundle not in s:
    raise SystemExit('Expected second featured-card anchor not found')
s = s.replace(old_bundle, product, 1)

s = s.replace('''                                  height: 320,
                                  child: ListView.separated(''','''                                  height: 274,
                                  child: ListView.separated(''',1)
s = s.replace('''                                      width: 174,
                                      height: 320,
                                      child: featuredOfferSections[index],''','''                                      width: 174,
                                      height: 258,
                                      child: featuredOfferSections[index],''',1)

home.write_text(s, encoding='utf-8')
print('All featured offer types now use the same 174x258 compact preview card.')
