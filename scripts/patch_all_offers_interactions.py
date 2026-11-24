from pathlib import Path
p = Path("astro_mobile/lib/screens/home_screen.dart")
s = p.read_text(encoding="utf-8")
dollar = chr(36)
marker = "  Future<List<Map<String, dynamic>>> _loadOffers() async {"
helpers = r"""
  Product _offerPricedProduct(Product p, double? sale) => Product(
    id:p.id, name:p.name, category:p.category, subcategoryId:p.subcategoryId,
    price:sale ?? p.price, imageUrl:p.imageUrl, images:p.images,
    description:p.description, isActive:p.isActive, colors:p.colors, brand:p.brand,
    rating:p.rating, reviewCount:p.reviewCount, stockQuantity:p.stockQuantity,
    isNew:p.isNew, rewardPoints:p.rewardPoints, salesCount:p.salesCount,
    allowPointsPayment:p.allowPointsPayment, specifications:p.specifications);

  void _openOfferProduct(Product p, double? sale) {
    Navigator.push(context, MaterialPageRoute(
      builder: (_) => ProductDetailScreen(product:_offerPricedProduct(p,sale))));
  }

  void _addOfferProduct(Product p, double? sale) {
    if (p.stockQuantity != null && p.stockQuantity! <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content:Text('هذا المنتج غير متوفر في المخزون حالياً')));
      return;
    }
    if (p.colors.isNotEmpty) {
      _openOfferProduct(p,sale);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content:Text('اختر لون المنتج من صفحة التفاصيل لإضافته إلى السلة')));
      return;
    }
    CartService.instance.add(_offerPricedProduct(p,sale),null);
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      duration:const Duration(seconds:2),
      content:Text('تمت إضافة ' + p.name + ' إلى السلة بسعر العرض'),
      action:SnackBarAction(label:'عرض السلة',onPressed:()=>Navigator.push(
        context,MaterialPageRoute(builder:(_)=>const CartScreen())))));
  }

"""
if "void _addOfferProduct(Product p, double? sale)" not in s:
    if marker not in s: raise SystemExit("Offers loader anchor missing")
    s = s.replace(marker, helpers + marker, 1)

old_image = """child: SizedBox(width: 64, height: 64,
                                      child: AstroCachedImage(imageUrl: product.imageUrl, fit: BoxFit.cover)),"""
new_image = """child: InkWell(
                                      onTap: type == 'bundle' ? null : () => _openOfferProduct(product, sale),
                                      child: SizedBox(width: 64, height: 64,
                                        child: AstroCachedImage(imageUrl: product.imageUrl, fit: BoxFit.cover))),"""
if old_image in s: s = s.replace(old_image,new_image,1)

old_name = """Expanded(child: Text(product.name, maxLines: 2, overflow: TextOverflow.ellipsis,
                                    style: const TextStyle(color: astroNavy, fontWeight: FontWeight.w700))),"""
new_name = """Expanded(child: InkWell(
                                    onTap: type == 'bundle' ? null : () => _openOfferProduct(product, sale),
                                    child: Text(product.name, maxLines: 2, overflow: TextOverflow.ellipsis,
                                      style: const TextStyle(color: astroNavy, fontWeight: FontWeight.w700)))),"""
if old_name in s: s = s.replace(old_name,new_name,1)

old_sale = """if (sale != null)
                                    Text('""" + dollar + """{sale.toStringAsFixed(0)} د.ل',
                                      style: const TextStyle(color: Color(0xFFD92D42), fontWeight: FontWeight.w900)),"""
new_sale = """if (sale != null && type != 'bundle') ...[
                                    Column(
                                      crossAxisAlignment: CrossAxisAlignment.end,
                                      children: [
                                        Text('""" + dollar + """{sale.toStringAsFixed(0)} د.ل',
                                          style: const TextStyle(color: Color(0xFFD92D42), fontWeight: FontWeight.w900, fontSize: 16)),
                                        if (product.price > sale)
                                          Row(
                                            mainAxisSize: MainAxisSize.min,
                                            children: [
                                              Text('""" + dollar + """{product.price.toStringAsFixed(0)}',
                                                style: const TextStyle(color: Colors.grey, fontSize: 12, decoration: TextDecoration.lineThrough)),
                                              const SizedBox(width: 6),
                                              Container(
                                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                                                decoration: BoxDecoration(color: const Color(0xFFFFE4E8), borderRadius: BorderRadius.circular(6)),
                                                child: Text(
                                                  '${(((product.price - sale) / product.price) * 100).round()}% خصم',
                                                  style: const TextStyle(color: Color(0xFFD92D42), fontSize: 11, fontWeight: FontWeight.w900)),
                                              ),
                                            ],
                                          ),
                                      ],
                                    ),
                                    IconButton(
                                      tooltip: 'إضافة إلى السلة',
                                      visualDensity: VisualDensity.compact,
                                      onPressed: () => _addOfferProduct(product, sale),
                                      icon: const Icon(Icons.add_shopping_cart_rounded, color: astroBlue)),
                                  ],"""
if old_sale in s: s = s.replace(old_sale,new_sale,1)

# The current offers list uses a compact price Text rather than the legacy old_sale template.
old_price_text = """Text('${(sale ?? product.price).toStringAsFixed(0)} د.ل',
                                        style: const TextStyle(color: Color(0xFFD92D42), fontWeight: FontWeight.w900)),"""
new_price_text = """Column(
                                        crossAxisAlignment: CrossAxisAlignment.end,
                                        mainAxisSize: MainAxisSize.min,
                                        children: [
                                          Text('${(sale ?? product.price).toStringAsFixed(0)} د.ل',
                                            style: const TextStyle(color: Color(0xFFD92D42), fontWeight: FontWeight.w900)),
                                          if (sale != null && product.price > sale && product.price > 0) ...[
                                            const SizedBox(height: 3),
                                            Text('${product.price.toStringAsFixed(0)} د.ل',
                                              style: const TextStyle(color: Colors.grey, fontSize: 11, decoration: TextDecoration.lineThrough)),
                                            const SizedBox(height: 3),
                                            Container(
                                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                                              decoration: BoxDecoration(color: const Color(0xFFFFE4E8), borderRadius: BorderRadius.circular(6)),
                                              child: Text('${(((product.price - sale) / product.price) * 100).round()}% خصم',
                                                style: const TextStyle(color: Color(0xFFD92D42), fontSize: 10, fontWeight: FontWeight.w900)),
                                            ),
                                          ],
                                        ],
                                      ),"""
if old_price_text in s:
    s = s.replace(old_price_text, new_price_text, 1)


old_cover = """                          child: Image.network(cover, height: 210, width: double.infinity, fit: BoxFit.contain,
                            errorBuilder: (_, __, ___) => const SizedBox(height: 100, child: Icon(Icons.card_giftcard, size: 42))),"""
new_cover = """                          child: InkWell(
                            onTap: productEntries.isEmpty ? null : () {
                              final first = productEntries.first;
                              final p = first['product'] as Product;
                              final item = first['item'] as Map<String, dynamic>;
                              if (type == 'bundle' && bundlePrice != null) {
                                final offerId = int.tryParse('${offer['id']}');
                                if (offerId == null) return;
                                Navigator.push(context, MaterialPageRoute(builder: (_) => BundleDetailsScreen(
                                  offerId: offerId,
                                  offerName: name,
                                  bundlePrice: bundlePrice,
                                  products: productEntries.map((e) {
                                    final p = e['product'] as Product;
                                    return <String, dynamic>{'name': p.name, 'imageUrl': p.imageUrl, 'description': p.description};
                                  }).toList(),
                                )));
                              } else {
                                _openOfferProduct(p, double.tryParse('""" + dollar + """{item['offer_price'] ?? ''}'));
                              }
                            },
                            child: Image.network(cover, height: 210, width: double.infinity, fit: BoxFit.contain,
                              errorBuilder: (_, __, ___) => const SizedBox(height: 100, child: Icon(Icons.card_giftcard, size: 42))),"""
if old_cover in s:
    s = s.replace(old_cover,new_cover,1)
    close = """                        ),
                      const SizedBox(height: 10),
                      Text(name,"""
    if close in s:
        s = s.replace(close,"""                          ),
                        ),
                      const SizedBox(height: 10),
                      Text(name,""",1)



p.write_text(s,encoding="utf-8")
print("Offer product rows now open details and include sale-price add-to-cart buttons.")
