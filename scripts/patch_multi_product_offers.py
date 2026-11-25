from pathlib import Path

root = Path('astro_mobile')

home_path = Path("astro_mobile/lib/screens/home_screen.dart")
cart_path = Path("astro_mobile/lib/services/cart_service.dart")
home = home_path.read_text()
cart = cart_path.read_text()

# Keep offer streams and their last successful snapshots stable across rebuilds
# and navigation away from / back to the home screen.
if "static late final Stream<List<Map<String, dynamic>>> _astroHomeOffersStream" not in home:
    nav_marker = "  int nav = 0;"
    if home.count(nav_marker) != 1:
        raise SystemExit("Could not locate the home state navigation field exactly once")
    home = home.replace(
        nav_marker,
        nav_marker + """
  static late final Stream<List<Map<String, dynamic>>> _astroHomeOffersStream =
      Supabase.instance.client.from('offers').stream(primaryKey: ['id']);
  static late final Stream<List<Map<String, dynamic>>> _astroHomeOfferItemsStream =
      Supabase.instance.client.from('offer_items').stream(primaryKey: ['id']);
  static List<Map<String, dynamic>> _cachedHomeOffers = [];
  static List<Map<String, dynamic>> _cachedHomeOfferItems = [];
""",
        1,
    )

if "final GlobalKey _homeOffersSectionKey" not in home:
    home = home.replace(
        "  int nav = 0;",
        "  int nav = 0;\n  final GlobalKey _homeOffersSectionKey = GlobalKey();",
        1,
    )

if "List<Map<String, dynamic>> _cachedHomeOffers" not in home:
    home = home.replace(
        "  final GlobalKey _homeOffersSectionKey = GlobalKey();",
        "  final GlobalKey _homeOffersSectionKey = GlobalKey();\n  List<Map<String, dynamic>> _cachedHomeOffers = [];\n  List<Map<String, dynamic>> _cachedHomeOfferItems = []",
        1,
    )

# Install the dedicated bundle checkout screen (cash or bank transfer only).
import shutil
checkout_source = Path("scripts/bundle_checkout_screen.dart")
checkout_target = root / "lib/screens/bundle_checkout_screen.dart"
if not checkout_source.exists():
    raise SystemExit("Bundle checkout screen source is missing")
shutil.copyfile(checkout_source, checkout_target)
checkout_import = "import 'bundle_checkout_screen.dart';"
if checkout_import not in home:
    home = home.replace("import 'account_screen.dart';", "import 'account_screen.dart';\n" + checkout_import, 1)


if "ASTRO_MULTI_PRODUCT_OFFERS_PATCH" not in home:
    offer_query = ".from('offers')"
    build_at = home.find("Widget build")
    query_at = home.find(offer_query, build_at if build_at >= 0 else 0)
    if query_at < 0:
        raise SystemExit("Could not locate the existing offers section in home_screen.dart")
    start = home.rfind("              SliverToBoxAdapter(", 0, query_at)
    end = home.find("SliverToBoxAdapter(", query_at)
    if end < 0:
        # The offers section can be the final sliver in the original home page.
        end = home.find("\\n            ],", query_at)
    if start < 0 or end < 0:
        raise SystemExit("Could not isolate the existing offers section safely")

    block = """              // ASTRO_MULTI_PRODUCT_OFFERS_PATCH
              SliverToBoxAdapter(
                key: _homeOffersSectionKey,
                child: StreamBuilder<List<Map<String, dynamic>>>(
                  stream: _astroHomeOffersStream,
                  initialData: _cachedHomeOffers.isEmpty ? null : _cachedHomeOffers,
                  builder: (context, offerSnapshot) {
                    if (offerSnapshot.hasData) _cachedHomeOffers = offerSnapshot.data!;
                    final now = DateTime.now();
                    final activeOffers = (_cachedHomeOffers).where((offer) {
                      final starts = DateTime.tryParse('${offer['starts_at'] ?? ''}');
                      final ends = DateTime.tryParse('${offer['ends_at'] ?? ''}');
                      return offer['is_active'] == true && starts != null && ends != null &&
                          !now.isBefore(starts) && now.isBefore(ends);
                    }).toList();

                    return StreamBuilder<List<Map<String, dynamic>>>(
                      stream: _astroHomeOfferItemsStream,
                      initialData: _cachedHomeOfferItems.isEmpty ? null : _cachedHomeOfferItems,
                      builder: (context, itemSnapshot) {
                        if (itemSnapshot.hasData) _cachedHomeOfferItems = itemSnapshot.data!;
                        final offerItems = _cachedHomeOfferItems;
                        final offerSections = <Widget>[];
                        final featuredOfferSections = <Widget>[];
                        // Newer campaigns take priority when multiple active campaigns include the same product.
                        final orderedOffers = [...activeOffers]
                          ..sort((a, b) => (DateTime.tryParse('${b['created_at'] ?? ''}') ?? DateTime.fromMillisecondsSinceEpoch(0))
                              .compareTo(DateTime.tryParse('${a['created_at'] ?? ''}') ?? DateTime.fromMillisecondsSinceEpoch(0)));
                        final claimedProducts = <String>{};

                        for (final offer in orderedOffers) {
                          final type = '${offer['offer_type'] ?? ''}';
                          final offerCards = <Widget>[];
                          final usedProducts = <String>{};

                          if (type == 'bundle') {
                            final offerId = '${offer['id']}';
                            final bundleItems = offerItems.where((row) => '${row['offer_id']}' == offerId).toList();
                            final bundleProductIds = bundleItems.map((row) => '${row['product_id'] ?? ''}').where((id) => id.isNotEmpty).toSet();
                            if (bundleProductIds.any(claimedProducts.contains)) continue;
                            final bundleEntries = <Map<String, dynamic>>[];
                            for (final item in bundleItems) {
                              final product = _findProduct(products, '${item['product_id'] ?? ''}');
                              if (product == null) continue;
                              bundleEntries.add({
                                'product': product,
                                'quantity': int.tryParse('${item['quantity'] ?? 1}') ?? 1,
                              });
                            }

                            if (bundleEntries.isNotEmpty) {
                              claimedProducts.addAll(bundleEntries.map((entry) => (entry['product'] as Product).id));
                              final startDate = DateTime.tryParse('${offer['starts_at'] ?? ''}')?.toLocal();
                              final endDate = DateTime.tryParse('${offer['ends_at'] ?? ''}')?.toLocal();
                              final offerName = '${offer['name'] ?? offer['title'] ?? 'باقة مميزة'}';
                              final period = startDate != null && endDate != null
                                  ? 'من ${startDate.day}/${startDate.month}/${startDate.year} إلى ${endDate.day}/${endDate.month}/${endDate.year}'
                                  : '';
                              final bundlePrice = double.tryParse('${offer['bundle_price'] ?? ''}') ?? 0;
                              final bundleProducts = bundleEntries.map((entry) => entry['product'] as Product).toList();

                              offerSections.add(
                                Padding(
                                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.stretch,
                                    children: [
                                      Row(
                                        children: [
                                          const Icon(Icons.card_giftcard_rounded, color: Color(0xFFE44755), size: 19),
                                          const SizedBox(width: 7),
                                          Expanded(
                                            child: Text(offerName, maxLines: 1, overflow: TextOverflow.ellipsis,
                                              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: astroNavy)),
                                          ),
                                          if (period.isNotEmpty)
                                            Text(period, style: const TextStyle(fontSize: 10, color: Colors.blueGrey, fontWeight: FontWeight.w600)),
                                        ],
                                      ),
                                      StreamBuilder<int>(
                                        stream: Stream.periodic(const Duration(seconds: 1), (tick) => tick),
                                        builder: (context, snapshot) {
                                          final remaining = endDate?.difference(DateTime.now());
                                          if (remaining == null) return const SizedBox.shrink();
                                          if (remaining.isNegative || remaining.inSeconds == 0) {
                                            return const Padding(
                                              padding: EdgeInsets.only(bottom: 8),
                                              child: Text('انتهى العرض', textAlign: TextAlign.right,
                                                style: TextStyle(color: Color(0xFFB42318), fontWeight: FontWeight.w800, fontSize: 12)),
                                            );
                                          }
                                          final days = remaining.inDays;
                                          final hours = remaining.inHours.remainder(24).toString().padLeft(2, '0');
                                          final minutes = remaining.inMinutes.remainder(60).toString().padLeft(2, '0');
                                          final seconds = remaining.inSeconds.remainder(60).toString().padLeft(2, '0');
                                          final value = days > 0 ? '$days يوم  $hours:$minutes:$seconds' : '$hours:$minutes:$seconds';
                                          return Align(
                                            alignment: Alignment.centerRight,
                                            child: Container(
                                              margin: const EdgeInsets.fromLTRB(10, 0, 10, 6),
                                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
                                              decoration: BoxDecoration(color: const Color(0xFFFFF0F1), borderRadius: BorderRadius.circular(10)),
                                              child: Text('ينتهي العرض خلال  $value',
                                                style: const TextStyle(color: Color(0xFFE44755), fontWeight: FontWeight.w900, fontSize: 12)),
                                            ),
                                          );
                                        },
                                      ),
                                      const SizedBox(height: 9),
                                      GridView.builder(
                                        shrinkWrap: true,
                                        physics: const NeverScrollableScrollPhysics(),
                                        itemCount: 1,
                                        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                                          crossAxisCount: 1,
                                          crossAxisSpacing: 0,
                                          mainAxisSpacing: 0,
                                          childAspectRatio: 0.90,
                                        ),
                                        itemBuilder: (context, index) {
                                          return Container(
                                            decoration: BoxDecoration(
                                              color: Colors.white,
                                              borderRadius: BorderRadius.circular(18),
                                              border: Border.all(color: const Color(0xFFDCE6F1)),
                                              boxShadow: const [BoxShadow(color: Color(0x0A12345A), blurRadius: 9, offset: Offset(0, 3))],
                                            ),
                                            padding: const EdgeInsets.all(10),
                                            child: Column(
                                              crossAxisAlignment: CrossAxisAlignment.stretch,
                                              children: [
                                                SizedBox(
                                                  height: 148,
                                                  child: Stack(
                                                    children: [
                                                      Positioned.fill(
                                                        child: Builder(
                                                          builder: (context) {
                                                            final coverUrl = (offer['cover_image_url'] ?? '').toString().trim();
                                                            if (coverUrl.isNotEmpty) {
                                                              // Preserve the full uploaded bundle cover without cropping it.
                                                              // Contain keeps text and product details inside wide promotional images visible.
                                                              return ClipRRect(
                                                                borderRadius: BorderRadius.circular(10),
                                                                child: Image.network(
                                                                  coverUrl,
                                                                  fit: BoxFit.contain,
                                                                  width: double.infinity,
                                                                  height: double.infinity,
                                                                  loadingBuilder: (context, child, progress) {
                                                                    if (progress == null) return child;
                                                                    return const ColoredBox(
                                                                      color: Color(0xFFF3F6FC),
                                                                      child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
                                                                    );
                                                                  },
                                                                  errorBuilder: (context, error, stackTrace) => Row(
                                                                    children: [
                                                                      for (final product in bundleProducts.take(3))
                                                                        Expanded(
                                                                          child: Padding(
                                                                            padding: const EdgeInsets.all(2),
                                                                            child: ClipRRect(
                                                                              borderRadius: BorderRadius.circular(9),
                                                                              child: AstroCachedImage(
                                                                                imageUrl: product.imageUrl,
                                                                                fit: BoxFit.cover,
                                                                                errorWidget: const ColoredBox(
                                                                                  color: Color(0xFFF1F4FA),
                                                                                  child: Center(child: Icon(Icons.card_giftcard_rounded, color: Color(0xFF8A9AAF), size: 34)),
                                                                                ),
                                                                              ),
                                                                            ),
                                                                          ),
                                                                        ),
                                                                    ],
                                                                  ),
                                                                ),
                                                              );
                                                            }
                                                            return Row(
                                                              children: [
                                                                for (final product in bundleProducts.take(3))
                                                                  Expanded(
                                                                    child: Padding(
                                                                      padding: const EdgeInsets.all(2),
                                                                      child: ClipRRect(
                                                                        borderRadius: BorderRadius.circular(9),
                                                                        child: AstroCachedImage(imageUrl: product.imageUrl, fit: BoxFit.cover),
                                                                      ),
                                                                    ),
                                                                  ),
                                                              ],
                                                            );
                                                          },
                                                        )
                                                      ),
                                                      Positioned(
                                                        top: 5, right: 5,
                                                        child: Container(
                                                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                                          decoration: BoxDecoration(color: const Color(0xFFE44755), borderRadius: BorderRadius.circular(20)),
                                                          child: Text('${bundleEntries.length} منتجات',
                                                            style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.w800)),
                                                        ),
                                                      ),
                                                    ],
                                                  ),
                                                ),
                                                const SizedBox(height: 8),
                                                Text(offerName, maxLines: 1, overflow: TextOverflow.ellipsis,
                                                  style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w900, color: astroNavy)),
                                                Text('${bundlePrice.toStringAsFixed(2)} د.ل',
                                                  style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w900, color: Color(0xFFE44755))),
                                                const SizedBox(height: 5),
                                                SizedBox(
                                                  height: 46,
                                                  child: ElevatedButton(
                                                    style: ElevatedButton.styleFrom(
                                                      backgroundColor: const Color(0xFF1765C5),
                                                      foregroundColor: Colors.white,
                                                      minimumSize: const Size(double.infinity, 46),
                                                      tapTargetSize: MaterialTapTargetSize.padded,
                                                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                                                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(9)),
                                                    ),
                                                    onPressed: () {
                                                      showModalBottomSheet<void>(
                                                        context: context,
                                                        isScrollControlled: true,
                                                        backgroundColor: Colors.transparent,
                                                        builder: (sheetContext) => DraggableScrollableSheet(
                                                          initialChildSize: 0.72,
                                                          minChildSize: 0.45,
                                                          maxChildSize: 0.92,
                                                          builder: (context, scrollController) => Container(
                                                            decoration: const BoxDecoration(
                                                              color: Colors.white,
                                                              borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
                                                            ),
                                                            child: Column(
                                                              children: [
                                                                const SizedBox(height: 10),
                                                                Container(width: 42, height: 4, decoration: BoxDecoration(color: Colors.black26, borderRadius: BorderRadius.circular(8))),
                                                                Padding(
                                                                  padding: const EdgeInsets.fromLTRB(18, 16, 18, 8),
                                                                  child: Row(
                                                                    children: [
                                                                      Expanded(child: Text(offerName, style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w900, color: astroNavy))),
                                                                      IconButton(onPressed: () => Navigator.pop(sheetContext), icon: const Icon(Icons.close)),
                                                                    ],
                                                                  ),
                                                                ),
                                                                Padding(
                                                                  padding: const EdgeInsets.symmetric(horizontal: 18),
                                                                  child: Align(alignment: Alignment.centerRight,
                                                                    child: Text('محتويات الباقة — اضغط على المنتج للتفاصيل',
                                                                      style: TextStyle(color: Colors.blueGrey.shade700, fontSize: 12))),
                                                                ),
                                                                Expanded(
                                                                  child: GridView.builder(
                                                                    controller: scrollController,
                                                                    padding: const EdgeInsets.all(14),
                                                                    itemCount: bundleEntries.length,
                                                                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                                                                      crossAxisCount: 2,
                                                                      crossAxisSpacing: 10,
                                                                      mainAxisSpacing: 10,
                                                                      childAspectRatio: 0.76,
                                                                    ),
                                                                    itemBuilder: (context, itemIndex) {
                                                                      final entry = bundleEntries[itemIndex];
                                                                      final product = entry['product'] as Product;
                                                                      final quantity = entry['quantity'] as int;
                                                                      return InkWell(
                                                                        borderRadius: BorderRadius.circular(14),
                                                                        onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ProductDetailScreen(product: product))),
                                                                        child: Container(
                                                                          padding: const EdgeInsets.all(9),
                                                                          decoration: BoxDecoration(
                                                                            color: const Color(0xFFF8FAFD),
                                                                            borderRadius: BorderRadius.circular(14),
                                                                            border: Border.all(color: const Color(0xFFE1E8F0)),
                                                                          ),
                                                                          child: Column(
                                                                            crossAxisAlignment: CrossAxisAlignment.stretch,
                                                                            children: [
                                                                              Expanded(child: ClipRRect(
                                                                                borderRadius: BorderRadius.circular(10),
                                                                                child: Image.network(product.imageUrl, fit: BoxFit.contain,
                                                                                  errorBuilder: (_, __, ___) => const Icon(Icons.image_not_supported_outlined)),
                                                                              )),
                                                                              const SizedBox(height: 7),
                                                                              Text(product.name, maxLines: 2, overflow: TextOverflow.ellipsis,
                                                                                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w800, color: astroNavy)),
                                                                              Text('الكمية: $quantity', style: const TextStyle(fontSize: 11, color: Colors.blueGrey)),
                                                                            ],
                                                                          ),
                                                                        ),
                                                                      );
                                                                    },
                                                                  ),
                                                                ),
                                                                SafeArea(
                                                                  top: false,
                                                                  child: Container(
                                                                    width: double.infinity,
                                                                    padding: const EdgeInsets.fromLTRB(18, 12, 18, 12),
                                                                    decoration: const BoxDecoration(
                                                                      color: Colors.white,
                                                                      border: Border(top: BorderSide(color: Color(0xFFE8EDF3))),
                                                                    ),
                                                                    child: Row(
                                                                      crossAxisAlignment: CrossAxisAlignment.center,
                                                                      children: [
                                                                        Expanded(
                                                                          child: Column(
                                                                            mainAxisSize: MainAxisSize.min,
                                                                            crossAxisAlignment: CrossAxisAlignment.start,
                                                                            children: [
                                                                              const Text('السعر الإجمالي للباقة',
                                                                                style: TextStyle(fontSize: 12, color: Colors.blueGrey, fontWeight: FontWeight.w600)),
                                                                              const SizedBox(height: 3),
                                                                              Text('${bundlePrice.toStringAsFixed(2)} د.ل',
                                                                                maxLines: 1, overflow: TextOverflow.ellipsis,
                                                                                style: const TextStyle(fontSize: 21, height: 1.15, fontWeight: FontWeight.w900, color: Color(0xFFE44755))),
                                                                            ],
                                                                          ),
                                                                        ),
                                                                        const SizedBox(width: 14),
                                                                        SizedBox(
                                                                          width: 154,
                                                                          height: 50,
                                                                          child: ElevatedButton(
                                                                            style: ElevatedButton.styleFrom(
                                                                              backgroundColor: const Color(0xFF1765C5),
                                                                              foregroundColor: Colors.white,
                                                                              elevation: 1,
                                                                              padding: const EdgeInsets.symmetric(horizontal: 10),
                                                                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                                                                            ),
                                                                            onPressed: int.tryParse(offer['id'].toString()) == null ? null : () {
                                                                              Navigator.push(context, MaterialPageRoute(builder: (_) => BundleCheckoutScreen(
                                                                                offerId: int.parse(offer['id'].toString()),
                                                                                offerName: offerName,
                                                                                bundlePrice: bundlePrice,
                                                                              )));
                                                                            },
                                                                            child: const Text('شراء الباقة',
                                                                              maxLines: 1, style: TextStyle(fontSize: 14, fontWeight: FontWeight.w900)),
                                                                          ),
                                                                        ),
                                                                      ],
                                                                    ),
                                                                  ),
                                                                ),
                                                              ],
                                                            ),
                                                          ),
                                                        ),
                                                      );
                                                    },
                                                    child: const Text('عرض التفاصيل', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w800)),
                                                  ),
                                                ),
                                              ],
                                            ),
                                          );
                                        },
                                      ),
                                    ],
                                  ),
                                ),
                              );
                              if (offer['show_on_home'] == true) featuredOfferSections.add(offerSections.last);
                            }
                            continue;
                          }

                          if (type == 'product') {
                            final offerId = '${offer['id']}';
                            for (final item in offerItems.where((row) => '${row['offer_id']}' == offerId)) {
                              final productId = '${item['product_id'] ?? ''}';
                              final product = _findProduct(products, productId);
                              final salePrice = double.tryParse('${item['offer_price'] ?? ''}');
                              if (product == null || salePrice == null || salePrice <= 0 ||
                                  salePrice >= product.price || usedProducts.contains(product.id) || claimedProducts.contains(product.id)) continue;
                              usedProducts.add(product.id);
                              claimedProducts.add(product.id);
                              offerCards.add(_offerProductCard(product, salePrice, 'سعر خاص'));
                            }

                            // Keep legacy single-product offers visible as before.
                            final legacyId = '${offer['product_id'] ?? ''}';
                            if (legacyId.isNotEmpty && !usedProducts.contains(legacyId) && !claimedProducts.contains(legacyId)) {
                              final product = _findProduct(products, legacyId);
                              final discountType = '${offer['discount_type'] ?? ''}';
                              final discountValue = double.tryParse('${offer['discount_value'] ?? ''}') ?? 0;
                              if (product != null && discountValue > 0) {
                                final salePrice = discountType == 'percentage'
                                    ? product.price * (1 - discountValue / 100)
                                    : discountValue;
                                if (salePrice > 0 && salePrice < product.price) {
                                  usedProducts.add(product.id);
                                  claimedProducts.add(product.id);
                                  offerCards.add(_offerProductCard(
                                    product, salePrice,
                                    discountType == 'percentage'
                                        ? 'خصم ${discountValue.toStringAsFixed(0)}%'
                                        : 'سعر خاص',
                                  ));
                                }
                              }
                            }
                          } else if (type == 'category') {
                            final discountType = '${offer['discount_type'] ?? ''}';
                            final discountValue = double.tryParse('${offer['discount_value'] ?? ''}') ?? 0;
                            if (discountValue <= 0) continue;
                            for (final product in products) {
                              if (product.category != '${offer['category_name'] ?? ''}' ||
                                  usedProducts.contains(product.id) || claimedProducts.contains(product.id)) continue;
                              final salePrice = discountType == 'percentage'
                                  ? product.price * (1 - discountValue / 100)
                                  : discountValue;
                              if (salePrice <= 0 || salePrice >= product.price) continue;
                              usedProducts.add(product.id);
                              claimedProducts.add(product.id);
                              offerCards.add(_offerProductCard(
                                product, salePrice,
                                discountType == 'percentage'
                                    ? 'خصم ${discountValue.toStringAsFixed(0)}%'
                                    : 'سعر خاص',
                              ));
                            }
                          }

                          if (offerCards.isNotEmpty) {
                            final startDate = DateTime.tryParse('${offer['starts_at'] ?? ''}')?.toLocal();
                            final endDate = DateTime.tryParse('${offer['ends_at'] ?? ''}')?.toLocal();
                            final offerName = '${offer['name'] ?? offer['title'] ?? 'عرض خاص'}';
                            final period = startDate != null && endDate != null
                                ? 'من ${startDate.day}/${startDate.month}/${startDate.year} إلى ${endDate.day}/${endDate.month}/${endDate.year}'
                                : '';

                            offerSections.add(
                              InkWell(
                                borderRadius: BorderRadius.circular(16),
                                onTap: () => Navigator.push(context, MaterialPageRoute(
                                  builder: (_) => _OfferProductsGridScreen(
                                    title: offerName,
                                    products: offerCards,
                                  ),
                                )),
                                child: Padding(
                                padding: const EdgeInsets.only(bottom: 14),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.stretch,
                                  children: [
                                    Padding(
                                      padding: const EdgeInsets.fromLTRB(10, 10, 10, 4),
                                      child: Row(
                                        children: [
                                          const Icon(Icons.local_offer_rounded, color: Color(0xFFE44755), size: 16),
                                          const SizedBox(width: 5),
                                          Expanded(
                                            child: Text(offerName,
                                              maxLines: 1,
                                              overflow: TextOverflow.ellipsis,
                                              style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w900, color: astroNavy)),
                                          ),
                                        ],
                                      ),
                                    ),
                                      StreamBuilder<int>(
                                        stream: Stream.periodic(const Duration(seconds: 1), (tick) => tick),
                                        builder: (context, snapshot) {
                                          final remaining = endDate?.difference(DateTime.now());
                                          if (remaining == null) return const SizedBox.shrink();
                                          if (remaining.isNegative || remaining.inSeconds == 0) {
                                            return const Padding(
                                              padding: EdgeInsets.only(bottom: 8),
                                              child: Text('انتهى العرض', textAlign: TextAlign.right,
                                                style: TextStyle(color: Color(0xFFB42318), fontWeight: FontWeight.w800, fontSize: 12)),
                                            );
                                          }
                                          final days = remaining.inDays;
                                          final hours = remaining.inHours.remainder(24).toString().padLeft(2, '0');
                                          final minutes = remaining.inMinutes.remainder(60).toString().padLeft(2, '0');
                                          final seconds = remaining.inSeconds.remainder(60).toString().padLeft(2, '0');
                                          final value = days > 0 ? '$days يوم  $hours:$minutes:$seconds' : '$hours:$minutes:$seconds';
                                          return Align(
                                            alignment: Alignment.centerRight,
                                            child: Container(
                                              margin: const EdgeInsets.fromLTRB(18, 0, 18, 8),
                                              padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 6),
                                              decoration: BoxDecoration(color: const Color(0xFFFFF0F1), borderRadius: BorderRadius.circular(10)),
                                              child: Text('ينتهي العرض خلال  $value',
                                                style: const TextStyle(color: Color(0xFFE44755), fontWeight: FontWeight.w900, fontSize: 10)),
                                            ),
                                          );
                                        },
                                      ),
                                    Builder(
                                      builder: (context) {
                                        final firstProduct = usedProducts.isNotEmpty
                                            ? _findProduct(products, usedProducts.first)
                                            : null;
                                        final coverUrl = (offer['cover_image_url'] ?? '').toString().trim();
                                        final imageUrl = coverUrl.isNotEmpty
                                            ? coverUrl
                                            : (firstProduct?.imageUrl ?? '');
                                        return Container(
                                          margin: const EdgeInsets.fromLTRB(12, 2, 12, 14),
                                          padding: const EdgeInsets.all(10),
                                          decoration: BoxDecoration(
                                            color: Colors.white,
                                            borderRadius: BorderRadius.circular(22),
                                            border: Border.all(color: const Color(0xFFDCE6F1)),
                                            boxShadow: const [BoxShadow(color: Color(0x1212345A), blurRadius: 14, offset: Offset(0, 5))],
                                          ),
                                          child: Column(
                                            crossAxisAlignment: CrossAxisAlignment.stretch,
                                            children: [
                                              ClipRRect(
                                                borderRadius: BorderRadius.circular(15),
                                                child: AspectRatio(
                                                  aspectRatio: 1.65,
                                                  child: imageUrl.isEmpty
                                                      ? Container(
                                                          color: const Color(0xFFF1F4FA),
                                                          child: const Icon(Icons.local_offer_rounded, color: Color(0xFF8A9AAF), size: 42),
                                                        )
                                                      : Container(
                                                          color: const Color(0xFF071B3B),
                                                          alignment: Alignment.center,
                                                          child: AstroCachedImage(
                                                            imageUrl: imageUrl,
                                                            fit: BoxFit.contain,
                                                            placeholder: const ColoredBox(
                                                              color: Color(0xFF071B3B),
                                                              child: Center(child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)),
                                                            ),
                                                            errorWidget: const ColoredBox(
                                                              color: Color(0xFFF1F4FA),
                                                              child: Center(child: Icon(Icons.local_offer_rounded, color: Color(0xFF8A9AAF), size: 42)),
                                                            ),
                                                          ),
                                                        ),
                                                ),
                                              ),
                                              const SizedBox(height: 12),
                                              Row(
                                                children: [
                                                  Expanded(
                                                    child: Text(offerName, maxLines: 2, overflow: TextOverflow.ellipsis,
                                                      style: const TextStyle(color: astroNavy, fontSize: 16, fontWeight: FontWeight.w900)),
                                                  ),
                                                  const SizedBox(width: 8),
                                                  Container(
                                                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                                                    decoration: BoxDecoration(color: const Color(0xFFEAF3FF), borderRadius: BorderRadius.circular(20)),
                                                    child: Text('${offerCards.length} منتجات',
                                                      style: const TextStyle(color: Color(0xFF1765C5), fontSize: 11, fontWeight: FontWeight.w900)),
                                                  ),
                                                ],
                                              ),
                                              const SizedBox(height: 10),
                                              SizedBox(
                                                height: 46,
                                                child: ElevatedButton(
                                                  style: ElevatedButton.styleFrom(
                                                    backgroundColor: const Color(0xFF1765C5),
                                                    foregroundColor: Colors.white,
                                                    elevation: 0,
                                                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                                    minimumSize: const Size(double.infinity, 42),
                                                    tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                                                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(11)),
                                                  ),
                                                  onPressed: () => Navigator.push(context, MaterialPageRoute(
                                                    builder: (_) => _OfferProductsGridScreen(title: offerName, products: offerCards),
                                                  )),
                                                  child: const Text('تصفح العرض', maxLines: 1,
                                                    style: TextStyle(color: Colors.white, fontSize: 13, height: 1.1, fontWeight: FontWeight.w800)),
                                                ),
                                              ),
                                            ],
                                          ),
                                        );
                                      },
                                    ),
                                  ],
                                ),
                                ),
                              ),
                            );
                              if (offer['show_on_home'] == true) featuredOfferSections.add(offerSections.last);
                          }
                        }

                        return Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            if (featuredOfferSections.isNotEmpty)
                              Padding(
                                padding: const EdgeInsets.fromLTRB(18, 14, 18, 8),
                                child: Row(
                                  children: [
                                    const Expanded(child: Text('عروض مختارة لك',
                                      style: TextStyle(color: astroNavy, fontSize: 18, fontWeight: FontWeight.w900))),
                                    TextButton(
                                      onPressed: () => Navigator.push(context, MaterialPageRoute(
                                        builder: (_) => _AllOffersScreen(products: products),
                                      )),
                                      child: const Text('عرض كل العروض'),
                                    ),
                                  ],
                                ),
                              ),
                            if (featuredOfferSections.isEmpty)
                              Padding(
                                padding: const EdgeInsets.fromLTRB(18, 20, 18, 10),
                                child: Container(
                                  height: 76,
                                  alignment: Alignment.center,
                                  decoration: BoxDecoration(
                                    color: const Color(0xFFFFF0F1),
                                    borderRadius: BorderRadius.circular(16),
                                    border: Border.all(color: const Color(0xFFFFD8DD)),
                                  ),
                                  child: const Text('ترقبوا عروض ASTRO MOBILE قريباً',
                                    style: TextStyle(color: astroNavy, fontWeight: FontWeight.w800)),
                                ),
                              )
                            else
                              Padding(
                                padding: const EdgeInsets.fromLTRB(8, 2, 8, 16),
                                child: SizedBox(
                                  height: 370,
                                  child: ListView.separated(
                                    scrollDirection: Axis.horizontal,
                                    physics: const BouncingScrollPhysics(),
                                    padding: const EdgeInsets.symmetric(horizontal: 6),
                                    itemCount: featuredOfferSections.length,
                                    separatorBuilder: (_, __) => const SizedBox(width: 10),
                                    itemBuilder: (context, index) => SizedBox(
                                      width: MediaQuery.of(context).size.width * 0.86,
                                      child: featuredOfferSections[index],
                                    ),
                                  ),
                                ),
                              ),
                          ],
                        );
                      },
                    );
                  },
                ),
              ),"""

    home = home[:start] + block + home[end:]
    helper = """  Product? _findProduct(List<Product> products, String id) {
    for (final product in products) {
      if (product.id == id) return product;
    }
    return null;
  }

  Product _productAtOfferPrice(Product product, double salePrice) {
    return Product(
      id: product.id, name: product.name, category: product.category,
      subcategoryId: product.subcategoryId, price: salePrice,
      imageUrl: product.imageUrl, images: product.images,
      description: product.description, isActive: product.isActive,
      colors: product.colors, brand: product.brand, rating: product.rating,
      reviewCount: product.reviewCount, stockQuantity: product.stockQuantity,
      isNew: product.isNew, rewardPoints: product.rewardPoints,
      salesCount: product.salesCount, allowPointsPayment: product.allowPointsPayment,
      specifications: product.specifications,
    );
  }

"""
    marker = "  Widget _offerProductCard(Product product, double salePrice, String label) {"
    if marker not in home:
        raise SystemExit("Could not find _offerProductCard to add sale-price helper")
    home = home.replace(marker, helper + marker, 1)
    old_tap = "onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ProductDetailScreen(product: product))),"
    new_tap = "onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ProductDetailScreen(product: _productAtOfferPrice(product, salePrice)))),"
    card_marker = "  Widget _offerProductCard(Product product, double salePrice, String label) {"
    card_start = home.find(card_marker)
    if card_start < 0:
        raise SystemExit("Could not find offer card method")
    card_tail = home[card_start:]
    if old_tap not in card_tail:
        raise SystemExit("Could not find offer card navigation to pass sale price")
    home = home[:card_start] + card_tail.replace(old_tap, new_tap, 1)

    # Use a compact portrait product tile that fits a two-column home grid.
    card_start = home.find(card_marker)
    card_end = home.find("\n  Widget _homeProductSection", card_start)
    if card_start < 0 or card_end < 0:
        raise SystemExit("Could not isolate the offer product card for grid redesign")
    grid_card = """  Widget _offerProductCard(Product product, double salePrice, String label) {
    final discount = product.price > 0
        ? (((product.price - salePrice) / product.price) * 100).round()
        : 0;
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ProductDetailScreen(product: _productAtOfferPrice(product, salePrice)))),
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0xFFFFD8DD)),
            boxShadow: const [BoxShadow(color: Color(0x08000000), blurRadius: 7, offset: Offset(0, 2))],
          ),
          padding: const EdgeInsets.all(8),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Expanded(
                flex: 6,
                child: Stack(
                  children: [
                    Positioned.fill(
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(11),
                        child: product.imageUrl.isEmpty
                            ? _placeholder(product.category, false)
                            : AstroCachedImage(imageUrl: product.imageUrl, fit: BoxFit.contain,
                                errorWidget: _placeholder(product.category, false)),
                      ),
                    ),
                    Positioned(
                      top: 6, right: 6,
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 4),
                        decoration: BoxDecoration(color: const Color(0xFFE44755), borderRadius: BorderRadius.circular(20)),
                        child: Text(label, maxLines: 1, overflow: TextOverflow.ellipsis,
                          style: const TextStyle(color: Colors.white, fontSize: 9, fontWeight: FontWeight.w900)),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 7),
              Text(product.name, maxLines: 2, overflow: TextOverflow.ellipsis,
                style: const TextStyle(color: astroNavy, fontSize: 11, fontWeight: FontWeight.w800)),
              const SizedBox(height: 3),
              Row(
                children: [
                  Flexible(child: Text('${salePrice.toStringAsFixed(0)} د.ل',
                    maxLines: 1, style: const TextStyle(color: Color(0xFFD92D42), fontSize: 14, fontWeight: FontWeight.w900))),
                  const SizedBox(width: 5),
                  if (discount > 0) Text('-${discount}%',
                    style: const TextStyle(color: Color(0xFFD92D42), fontSize: 10, fontWeight: FontWeight.w800)),
                ],
              ),
              Text('${product.price.toStringAsFixed(0)} د.ل',
                style: const TextStyle(color: Colors.black38, fontSize: 10, decoration: TextDecoration.lineThrough)),
            ],
          ),
        ),
      ),
    );
  }

"""
    home = home[:card_start] + grid_card + home[card_end:]
    # The all-offers page owns its database reads. Never pass prebuilt widgets
    # from the home page: that builder is not mounted when the user opens the
    # Categories tab, which left the offers route with an empty widget list.
    all_offers_screen = """
class _AllOffersScreen extends StatefulWidget {
  final List<Product> products;
  const _AllOffersScreen({required this.products});
  @override
  State<_AllOffersScreen> createState() => _AllOffersScreenState();
}

class _AllOffersScreenState extends State<_AllOffersScreen> {
  late Future<List<Map<String, dynamic>>> _offersFuture;
  @override
  void initState() { super.initState(); _offersFuture = _loadOffers(); }

  Future<List<Map<String, dynamic>>> _loadOffers() async {
    final client = Supabase.instance.client;
    final results = await Future.wait([
      client.from('offers').select('*').eq('is_active', true).order('created_at', ascending: false),
      client.from('offer_items').select('*'),
    ]);
    final now = DateTime.now();
    final allOffers = List<Map<String, dynamic>>.from(results[0] as List);
    final allItems = List<Map<String, dynamic>>.from(results[1] as List);
    return allOffers.where((offer) {
      final starts = DateTime.tryParse('${offer['starts_at'] ?? ''}')?.toLocal();
      final ends = DateTime.tryParse('${offer['ends_at'] ?? ''}')?.toLocal();
      return starts != null && ends != null && !now.isBefore(starts) && now.isBefore(ends);
    }).map((offer) {
      final id = '${offer['id']}';
      return <String, dynamic>{...offer, '_items': allItems.where((item) => '${item['offer_id']}' == id).toList()};
    }).toList();
  }

  void _openOffer(Map<String, dynamic> offer) {
    final type = '${offer['offer_type'] ?? ''}';
    final items = List<Map<String, dynamic>>.from(offer['_items'] as List);
    final entries = <Map<String, dynamic>>[];
    for (final item in items) {
      for (final product in widget.products) {
        if (product.id == '${item['product_id'] ?? ''}') {
          entries.add({'product': product, 'item': item});
          break;
        }
      }
    }
    final name = '${offer['name'] ?? 'عرض خاص'}';
    final bundlePrice = double.tryParse('${offer['bundle_price'] ?? ''}');
    if (type == 'bundle' && bundlePrice != null) {
      final offerId = int.tryParse('${offer['id']}');
      if (offerId == null) return;
      Navigator.push(context, MaterialPageRoute(builder: (_) => BundleDetailsScreen(
        offerId: offerId, offerName: name, bundlePrice: bundlePrice,
        products: entries.map((e) {
          final p = e['product'] as Product;
          return <String, dynamic>{'name': p.name, 'imageUrl': p.imageUrl, 'description': p.description};
        }).toList(),
      )));
      return;
    }
    final categoryProducts = type == 'category'
        ? widget.products.where((p) => p.category == '${offer['category_name'] ?? ''}').toList()
        : <Product>[];
    Navigator.push(context, MaterialPageRoute(builder: (_) => _OfferContentsScreen(
      title: name, offer: offer, entries: entries, categoryProducts: categoryProducts,
    )));
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: astroBackground,
    appBar: AppBar(title: const Text('العروض والخصومات'), backgroundColor: astroBackground, foregroundColor: Colors.white, elevation: 0),
    body: FutureBuilder<List<Map<String, dynamic>>>(
      future: _offersFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) return const Center(child: CircularProgressIndicator());
        if (snapshot.hasError) return Center(child: Padding(padding: const EdgeInsets.all(24), child: Text('تعذر تحميل العروض: ${snapshot.error}', textAlign: TextAlign.center)));
        final offers = snapshot.data ?? [];
        if (offers.isEmpty) return const Center(child: Text('لا توجد عروض نشطة حالياً'));
        return RefreshIndicator(
          onRefresh: () async { setState(() { _offersFuture = _loadOffers(); }); await _offersFuture; },
          child: ListView.separated(
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 28), itemCount: offers.length,
            separatorBuilder: (_, __) => const SizedBox(height: 12),
            itemBuilder: (context, index) {
              final offer = offers[index];
              final name = '${offer['name'] ?? 'عرض خاص'}';
              final type = '${offer['offer_type'] ?? ''}';
              final cover = '${offer['cover_image_url'] ?? ''}'.trim();
              final items = List<Map<String, dynamic>>.from(offer['_items'] as List);
              final count = type == 'category'
                  ? widget.products.where((p) => p.category == '${offer['category_name'] ?? ''}').length
                  : items.length;
              final bundlePrice = double.tryParse('${offer['bundle_price'] ?? ''}');
              Product? firstProduct;
              if (items.isNotEmpty) {
                for (final p in widget.products) { if (p.id == '${items.first['product_id'] ?? ''}') { firstProduct = p; break; } }
              }
              final fallbackImageUrl = (firstProduct?.imageUrl ?? '').trim();
              final imageUrl = cover.isNotEmpty ? cover : fallbackImageUrl;
              final fallbackImage = fallbackImageUrl.isEmpty
                  ? const ColoredBox(color: Color(0xFF0B1B49), child: Center(child: Icon(Icons.local_offer_rounded, size: 44, color: astroBlue)))
                  : AstroCachedImage(
                      imageUrl: fallbackImageUrl,
                      fit: BoxFit.contain,
                      errorWidget: const ColoredBox(color: Color(0xFF0B1B49), child: Center(child: Icon(Icons.local_offer_rounded, size: 44, color: astroBlue))),
                    );
              return Material(
                color: const Color(0xFF0B1B49), borderRadius: BorderRadius.circular(20),
                child: InkWell(
                  borderRadius: BorderRadius.circular(20), onTap: () => _openOffer(offer),
                  child: Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(borderRadius: BorderRadius.circular(20), border: Border.all(color: const Color(0xFFDCE6F1)), boxShadow: const [BoxShadow(color: Color(0x0A12345A), blurRadius: 8, offset: Offset(0, 3))]),
                    child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                      ClipRRect(
                        borderRadius: BorderRadius.circular(14),
                        child: AspectRatio(
                          aspectRatio: 1.65,
                          child: imageUrl.isEmpty
                              ? fallbackImage
                              : AstroCachedImage(imageUrl: imageUrl, fit: BoxFit.contain, errorWidget: fallbackImage),
                        ),
                      ),
                      const SizedBox(height: 12),
                      Row(children: [
                        Expanded(child: Text(name, textAlign: TextAlign.right, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(color: astroNavy, fontSize: 18, fontWeight: FontWeight.w900))),
                        const SizedBox(width: 8),
                        Container(padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6), decoration: BoxDecoration(color: const Color(0xFFEAF3FF), borderRadius: BorderRadius.circular(20)), child: Text('$count منتجات', style: const TextStyle(color: astroBlue, fontSize: 12, fontWeight: FontWeight.w800))),
                      ]),
                      if (type == 'bundle' && bundlePrice != null)
                        Padding(padding: const EdgeInsets.only(top: 5), child: Text('${bundlePrice.toStringAsFixed(2)} د.ل', textAlign: TextAlign.right, style: const TextStyle(color: Color(0xFFD92D42), fontSize: 19, fontWeight: FontWeight.w900))),
                      const SizedBox(height: 10),
                      SizedBox(height: 48, child: ElevatedButton(
                        style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF1765C5), foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
                        onPressed: () => _openOffer(offer), child: const Text('تصفح العرض', style: TextStyle(fontWeight: FontWeight.w900)),
                      )),
                    ]),
                  ),
                ),
              );
            },
          ),
        );
      },
    ),
  );
}

class _OfferContentsScreen extends StatelessWidget {
  final String title;
  final Map<String, dynamic> offer;
  final List<Map<String, dynamic>> entries;
  final List<Product> categoryProducts;
  const _OfferContentsScreen({required this.title, required this.offer, required this.entries, required this.categoryProducts});

  Product _atPrice(Product p, double price) => Product(
    id: p.id, name: p.name, category: p.category, subcategoryId: p.subcategoryId, price: price,
    imageUrl: p.imageUrl, images: p.images, description: p.description, isActive: p.isActive,
    colors: p.colors, brand: p.brand, rating: p.rating, reviewCount: p.reviewCount,
    stockQuantity: p.stockQuantity, isNew: p.isNew, rewardPoints: p.rewardPoints,
    salesCount: p.salesCount, allowPointsPayment: p.allowPointsPayment, specifications: p.specifications,
  );

  @override
  Widget build(BuildContext context) {
    final type = '${offer['offer_type'] ?? ''}';
    final discount = double.tryParse('${offer['discount_value'] ?? ''}') ?? 0;
    final rows = entries.isNotEmpty ? entries : categoryProducts.map((p) => <String, dynamic>{'product': p, 'item': <String, dynamic>{}}).toList();
    return Scaffold(
      backgroundColor: const Color(0xFFF3F6FC),
      appBar: AppBar(title: Text(title), backgroundColor: Colors.white, foregroundColor: astroNavy, elevation: 0),
      body: rows.isEmpty ? const Center(child: Text('لا توجد منتجات متاحة في هذا العرض')) : ListView.separated(
        padding: const EdgeInsets.all(14), itemCount: rows.length, separatorBuilder: (_, __) => const SizedBox(height: 10),
        itemBuilder: (context, index) {
          final p = rows[index]['product'] as Product;
          final item = rows[index]['item'] as Map<String, dynamic>;
          final explicitSale = double.tryParse('${item['offer_price'] ?? ''}');
          final sale = explicitSale ?? (type == 'category' && discount > 0 ? p.price * (1 - discount / 100) : p.price);
          final discounted = sale > 0 && sale < p.price;
          return Material(color: Colors.white, borderRadius: BorderRadius.circular(16), child: InkWell(
            borderRadius: BorderRadius.circular(16),
            onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ProductDetailScreen(product: discounted ? _atPrice(p, sale) : p))),
            child: Padding(padding: const EdgeInsets.all(10), child: Row(children: [
              ClipRRect(borderRadius: BorderRadius.circular(10), child: SizedBox(width: 82, height: 82, child: AstroCachedImage(imageUrl: p.imageUrl, fit: BoxFit.cover))),
              const SizedBox(width: 12),
              Expanded(child: Text(p.name, maxLines: 3, overflow: TextOverflow.ellipsis, style: const TextStyle(color: astroNavy, fontWeight: FontWeight.w800))),
              const SizedBox(width: 8),
              Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
                Text('${sale.toStringAsFixed(0)} د.ل', style: const TextStyle(color: Color(0xFFD92D42), fontWeight: FontWeight.w900)),
                if (discounted) ...[
                  Text('${p.price.toStringAsFixed(0)} د.ل', style: const TextStyle(color: Colors.grey, fontSize: 11, decoration: TextDecoration.lineThrough)),
                  Text('خصم ${(((p.price - sale) / p.price) * 100).round()}%', style: const TextStyle(color: Color(0xFFD92D42), fontSize: 11, fontWeight: FontWeight.w800)),
                ],
              ]),
            ])),
          ));
        },
      ),
    );
  }
}
"""
    home += "\n" + all_offers_screen + "\n"

    if "class _OfferProductsGridScreen extends StatelessWidget" not in home:
        home += """

class _OfferProductsGridScreen extends StatelessWidget {
  final String title;
  final List<Widget> products;

  const _OfferProductsGridScreen({
    required this.title,
    required this.products,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF3F6FC),
      appBar: AppBar(
        title: Text(title, maxLines: 1, overflow: TextOverflow.ellipsis),
        backgroundColor: Colors.white,
        foregroundColor: astroNavy,
        elevation: 0,
      ),
      body: products.isEmpty
          ? const Center(child: Text('لا توجد منتجات متاحة في هذا العرض'))
          : GridView.builder(
              padding: const EdgeInsets.all(12),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                crossAxisSpacing: 10,
                mainAxisSpacing: 12,
                childAspectRatio: 0.72,
              ),
              itemCount: products.length,
              itemBuilder: (context, index) => products[index],
            ),
    );
  }
}

"""
    home_path.write_text(home)

# Retain the last successful product snapshot in memory when HomeScreen is
# rebuilt after navigating to another tab. This avoids blank/grey content while
# the realtime stream reconnects.
if "static List<Product> _cachedHomeProducts = [];" not in home:
    cache_marker = "  static List<Map<String, dynamic>> _cachedHomeOfferItems = [];"
    if home.count(cache_marker) != 1:
        raise SystemExit("Could not locate the home offers cache fields")
    home = home.replace(cache_marker, cache_marker + "\n  static List<Product> _cachedHomeProducts = [];", 1)

old_products_stream = """        return StreamBuilder<List<Product>>(
          stream: _productsStream,
          builder: (context, snapshot) {
            final sourceProducts = snapshot.data ?? [];"""
new_products_stream = """        return StreamBuilder<List<Product>>(
          stream: _productsStream,
          initialData: _cachedHomeProducts.isEmpty ? null : _cachedHomeProducts,
          builder: (context, snapshot) {
            if (snapshot.hasData && snapshot.data!.isNotEmpty) {
              _cachedHomeProducts = snapshot.data!;
            }
            final sourceProducts = snapshot.data ?? _cachedHomeProducts;"""
if old_products_stream in home:
    home = home.replace(old_products_stream, new_products_stream, 1)
elif new_products_stream not in home:
    raise SystemExit("Could not locate the home product StreamBuilder safely")

home_path.write_text(home)

if "item.product?.price == product.price" not in cart:
    old_match = "(item) => !item.isInquiryOption && item.product?.id == product.id && item.color == color,"
    new_match = "(item) => !item.isInquiryOption && item.product?.id == product.id &&\n          item.product?.price == product.price && item.color == color,"
    if old_match not in cart:
        raise SystemExit("Could not find cart item matching logic")
    cart_path.write_text(cart.replace(old_match, new_match, 1))

print("Multi-product offer cards and discounted cart price patch applied.")


# Install interactions on the dedicated all-offers page as part of the same build.
import runpy
runpy.run_path("scripts/patch_all_offers_interactions.py")
