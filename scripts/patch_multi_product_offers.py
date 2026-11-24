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
        "  final GlobalKey _homeOffersSectionKey = GlobalKey();\\n  List<Map<String, dynamic>> _cachedHomeOffers = [];\\n  List<Map<String, dynamic>> _cachedHomeOfferItems = [];",
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
    query_at = home.find(offer_query)
    if query_at < 0:
        raise SystemExit("Could not locate the existing offers section in home_screen.dart")
    start = home.rfind("              SliverToBoxAdapter(", 0, query_at)
    end = home.find("\n\n              SliverToBoxAdapter(", query_at)
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
                                              margin: const EdgeInsets.fromLTRB(18, 0, 18, 8),
                                              padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 6),
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
                                          crossAxisCount: 2,
                                          crossAxisSpacing: 10,
                                          mainAxisSpacing: 10,
                                          childAspectRatio: 0.88,
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
                                                Expanded(
                                                  child: Stack(
                                                    children: [
                                                      Positioned.fill(
                                                        child: FutureBuilder<Map<String, dynamic>?>(
                                                          future: Supabase.instance.client
                                                              .from('offers')
                                                              .select('cover_image_url')
                                                              .eq('id', offer['id'])
                                                              .maybeSingle(),
                                                          builder: (context, coverSnapshot) {
                                                            final coverUrl = (coverSnapshot.data?['cover_image_url'] ??
                                                                    offer['cover_image_url'] ?? '')
                                                                .toString().trim();
                                                            if (coverUrl.isNotEmpty) {
                                                              return ClipRRect(
                                                                borderRadius: BorderRadius.circular(10),
                                                                child: Image.network(
                                                                  coverUrl,
                                                                  key: ValueKey(coverUrl),
                                                                  fit: BoxFit.cover,
                                                                  errorBuilder: (_, __, ___) => const ColoredBox(
                                                                    color: Color(0xFFF0F3F8),
                                                                    child: Icon(Icons.image_outlined),
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
                                                                          child: Image.network(product.imageUrl, fit: BoxFit.cover,
                                                                            errorBuilder: (_, __, ___) => const ColoredBox(color: Color(0xFFF0F3F8), child: Icon(Icons.image_outlined))),
                                                                        ),
                                                                      ),
                                                                    ),
                                                                ],
                                                              );
                                                          },
                                                        ),
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
                                                  height: 34,
                                                  child: ElevatedButton(
                                                    style: ElevatedButton.styleFrom(
                                                      backgroundColor: const Color(0xFF1765C5),
                                                      foregroundColor: Colors.white,
                                                      padding: const EdgeInsets.symmetric(horizontal: 8),
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
                                      padding: const EdgeInsets.fromLTRB(18, 16, 18, 8),
                                      child: Row(
                                        children: [
                                          const Icon(Icons.local_offer_rounded, color: Color(0xFFE44755), size: 19),
                                          const SizedBox(width: 8),
                                          Expanded(
                                            child: Text(offerName,
                                              maxLines: 1,
                                              overflow: TextOverflow.ellipsis,
                                              style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w900, color: astroNavy)),
                                          ),
                                          if (period.isNotEmpty)
                                            Text(period,
                                              style: const TextStyle(fontSize: 11, color: Colors.blueGrey, fontWeight: FontWeight.w600)),
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
                                                style: const TextStyle(color: Color(0xFFE44755), fontWeight: FontWeight.w900, fontSize: 12)),
                                            ),
                                          );
                                        },
                                      ),
                                    SizedBox(
                                      height: 164,
                                      child: ListView.separated(
                                        padding: const EdgeInsets.symmetric(horizontal: 16),
                                        scrollDirection: Axis.horizontal,
                                        itemCount: offerCards.length,
                                        separatorBuilder: (_, __) => const SizedBox(width: 11),
                                        itemBuilder: (_, index) => offerCards[index],
                                      ),
                                    ),
                                  ],
                                ),
                                ),
                              ),
                            );
                          }
                        }

                        return Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            if (offerSections.isEmpty)
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
                              SizedBox(
                                height: 300,
                                child: ListView.separated(
                                  scrollDirection: Axis.horizontal,
                                  padding: const EdgeInsets.symmetric(horizontal: 16),
                                  itemCount: offerSections.length,
                                  separatorBuilder: (_, __) => const SizedBox(width: 12),
                                  itemBuilder: (context, index) => SizedBox(
                                    width: 318,
                                    child: offerSections[index],
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
    if "class _OfferProductsGridScreen extends StatelessWidget" not in home:
        home += "\n" + "\nclass _OfferProductsGridScreen extends StatelessWidget {\n  final String title;\n  final List<Widget> products;\n\n  const _OfferProductsGridScreen({\n    required this.title,\n    required this.products,\n  });\n\n  @override\n  Widget build(BuildContext context) {\n    return Scaffold(\n      backgroundColor: const Color(0xFFF3F6FC),\n      appBar: AppBar(\n        title: Text(title, maxLines: 1, overflow: TextOverflow.ellipsis),\n        backgroundColor: Colors.white,\n        foregroundColor: astroNavy,\n        elevation: 0,\n      ),\n      body: products.isEmpty\n          ? const Center(child: Text('لا توجد منتجات متاحة في هذا العرض'))\n          : GridView.builder(\n              padding: const EdgeInsets.all(12),\n              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(\n                crossAxisCount: 2,\n                crossAxisSpacing: 10,\n                mainAxisSpacing: 12,\n                childAspectRatio: 0.72,\n              ),\n              itemCount: products.length,\n              itemBuilder: (context, index) => products[index],\n            ),\n    );\n  }\n}\n\n"
    home_path.write_text(home)

if "item.product?.price == product.price" not in cart:
    old_match = "(item) => !item.isInquiryOption && item.product?.id == product.id && item.color == color,"
    new_match = "(item) => !item.isInquiryOption && item.product?.id == product.id &&\n          item.product?.price == product.price && item.color == color,"
    if old_match not in cart:
        raise SystemExit("Could not find cart item matching logic")
    cart_path.write_text(cart.replace(old_match, new_match, 1))

print("Multi-product offer cards and discounted cart price patch applied.")
