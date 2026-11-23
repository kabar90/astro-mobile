from pathlib import Path

home_path = Path("astro_mobile/lib/screens/home_screen.dart")
cart_path = Path("astro_mobile/lib/services/cart_service.dart")
home = home_path.read_text()
cart = cart_path.read_text()

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
                child: StreamBuilder<List<Map<String, dynamic>>>(
                  stream: Supabase.instance.client.from('offers').stream(primaryKey: ['id']),
                  builder: (context, offerSnapshot) {
                    final now = DateTime.now();
                    final activeOffers = (offerSnapshot.data ?? []).where((offer) {
                      final starts = DateTime.tryParse('${offer['starts_at'] ?? ''}');
                      final ends = DateTime.tryParse('${offer['ends_at'] ?? ''}');
                      return offer['is_active'] == true && starts != null && ends != null &&
                          !now.isBefore(starts) && now.isBefore(ends);
                    }).toList();

                    return StreamBuilder<List<Map<String, dynamic>>>(
                      stream: Supabase.instance.client.from('offer_items').stream(primaryKey: ['id']),
                      builder: (context, itemSnapshot) {
                        final offerItems = itemSnapshot.data ?? [];
                        final offerCards = <Widget>[];
                        final usedProducts = <String>{};

                        for (final offer in activeOffers) {
                          final type = '${offer['offer_type'] ?? ''}';
                          if (type == 'bundle') continue;

                          if (type == 'product') {
                            final offerId = '${offer['id']}';
                            for (final item in offerItems.where((row) => '${row['offer_id']}' == offerId)) {
                              final productId = '${item['product_id'] ?? ''}';
                              final product = _findProduct(products, productId);
                              final salePrice = double.tryParse('${item['offer_price'] ?? ''}');
                              if (product == null || salePrice == null || salePrice <= 0 ||
                                  salePrice >= product.price || usedProducts.contains(product.id)) continue;
                              usedProducts.add(product.id);
                              offerCards.add(_offerProductCard(product, salePrice, 'سعر خاص'));
                            }

                            // Keep legacy single-product offers visible as before.
                            final legacyId = '${offer['product_id'] ?? ''}';
                            if (legacyId.isNotEmpty && !usedProducts.contains(legacyId)) {
                              final product = _findProduct(products, legacyId);
                              final discountType = '${offer['discount_type'] ?? ''}';
                              final discountValue = double.tryParse('${offer['discount_value'] ?? ''}') ?? 0;
                              if (product != null && discountValue > 0) {
                                final salePrice = discountType == 'percentage'
                                    ? product.price * (1 - discountValue / 100)
                                    : discountValue;
                                if (salePrice > 0 && salePrice < product.price) {
                                  usedProducts.add(product.id);
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
                                  usedProducts.contains(product.id)) continue;
                              final salePrice = discountType == 'percentage'
                                  ? product.price * (1 - discountValue / 100)
                                  : discountValue;
                              if (salePrice <= 0 || salePrice >= product.price) continue;
                              usedProducts.add(product.id);
                              offerCards.add(_offerProductCard(
                                product, salePrice,
                                discountType == 'percentage'
                                    ? 'خصم ${discountValue.toStringAsFixed(0)}%'
                                    : 'سعر خاص',
                              ));
                            }
                          }
                        }

                        return Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            Padding(
                              padding: const EdgeInsets.fromLTRB(18, 20, 18, 8),
                              child: Row(
                                children: const [
                                  Text('العروض والتخفيضات', style: TextStyle(fontSize: 19, fontWeight: FontWeight.w900, color: astroNavy)),
                                  Spacer(),
                                  Icon(Icons.local_offer_rounded, color: Color(0xFFE44755), size: 20),
                                ],
                              ),
                            ),
                            if (offerCards.isEmpty)
                              Padding(
                                padding: const EdgeInsets.fromLTRB(18, 4, 18, 10),
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
    if old_tap not in home:
        raise SystemExit("Could not find offer card navigation to pass sale price")
    home = home.replace(old_tap, new_tap, 1)
    home_path.write_text(home)

if "item.product?.price == product.price" not in cart:
    old_match = "(item) => !item.isInquiryOption && item.product?.id == product.id && item.color == color,"
    new_match = "(item) => !item.isInquiryOption && item.product?.id == product.id &&\n          item.product?.price == product.price && item.color == color,"
    if old_match not in cart:
        raise SystemExit("Could not find cart item matching logic")
    cart_path.write_text(cart.replace(old_match, new_match, 1))

print("Multi-product offer cards and discounted cart price patch applied.")
