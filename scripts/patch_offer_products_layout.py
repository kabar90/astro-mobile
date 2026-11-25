from pathlib import Path

p = Path("astro_mobile/lib/screens/home_screen.dart")
s = p.read_text(encoding="utf-8")

start = s.find("class _OfferContentsScreen extends StatelessWidget")
if start < 0:
    raise SystemExit("Could not find _OfferContentsScreen")

# Change only the product rows shown after opening an offer. Every active offer
# (including future offers created from the dashboard) uses this same template.
old_scaffold = """    return Scaffold(
      backgroundColor: const Color(0xFFF3F6FC),
      appBar: AppBar(title: Text(title), backgroundColor: Colors.white, foregroundColor: astroNavy, elevation: 0),"""
new_scaffold = """    return Scaffold(
      backgroundColor: astroBackground,
      appBar: AppBar(title: Text(title), backgroundColor: astroBackground, foregroundColor: Colors.white, elevation: 0),"""
if old_scaffold in s[start:]:
    s = s[:start] + s[start:].replace(old_scaffold, new_scaffold, 1)
elif "backgroundColor: astroBackground" not in s[start:]:
    raise SystemExit("Offer contents scaffold anchor not found")

old_row = """          return Material(color: Colors.white, borderRadius: BorderRadius.circular(16), child: InkWell(
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
          ));"""
new_row = """          return Material(
            color: const Color(0xFF0B1B49),
            borderRadius: BorderRadius.circular(22),
            child: InkWell(
              borderRadius: BorderRadius.circular(22),
              onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ProductDetailScreen(product: discounted ? _atPrice(p, sale) : p))),
              child: Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: const Color(0xFF0B1B49),
                  borderRadius: BorderRadius.circular(22),
                  border: Border.all(color: const Color(0xFF17366F), width: 1),
                ),
                child: Row(
                  children: [
                    // In the app's RTL layout the image is kept at the left edge,
                    // matching the horizontal product cards used by the sections.
                    ClipRRect(
                      borderRadius: BorderRadius.circular(16),
                      child: SizedBox(
                        width: 112,
                        height: 112,
                        child: AstroCachedImage(imageUrl: p.imageUrl, fit: BoxFit.contain),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        p.name,
                        maxLines: 3,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w800, height: 1.35),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text('${sale.toStringAsFixed(0)} د.ل',
                          style: const TextStyle(color: Color(0xFFE44755), fontSize: 16, fontWeight: FontWeight.w900)),
                        if (discounted) ...[
                          const SizedBox(height: 5),
                          Text('${p.price.toStringAsFixed(0)} د.ل',
                            style: const TextStyle(color: Colors.white54, fontSize: 11, decoration: TextDecoration.lineThrough)),
                          const SizedBox(height: 3),
                          Text('خصم ${(((p.price - sale) / p.price) * 100).round()}%',
                            style: const TextStyle(color: Color(0xFFE44755), fontSize: 12, fontWeight: FontWeight.w900)),
                        ],
                      ],
                    ),
                  ],
                ),
              ),
            ),
          );"""
if old_row not in s[start:]:
    if "color: const Color(0xFF0B1B49)" not in s[start:]:
        raise SystemExit("Offer product row template anchor not found")
else:
    s = s[:start] + s[start:].replace(old_row, new_row, 1)

p.write_text(s, encoding="utf-8")
print("All products inside offer details now use the dark horizontal category-style card.")
