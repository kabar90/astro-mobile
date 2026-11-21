from pathlib import Path

dart = Path("astro_mobile/lib/screens/product_inquiry_inline.dart")
source = dart.read_text(encoding="utf-8")

anchor = """    final reply = (item['admin_reply'] ?? '').toString().trim();
    final ids = item['recommended_product_ids'];
"""
replacement = """    final reply = (item['admin_reply'] ?? '').toString().trim();
    final ids = item['recommended_product_ids'];
    final rawImages = item['admin_image_items'];
    final List<Map<String, dynamic>> replyImages = rawImages is List
        ? rawImages.whereType<Map>().map((e) => Map<String, dynamic>.from(e))
            .where((e) => (e['url'] ?? '').toString().trim().isNotEmpty).toList()
        : (item['admin_image_urls'] is List
            ? (item['admin_image_urls'] as List)
                .where((e) => e != null && e.toString().trim().isNotEmpty)
                .map((url) => <String, dynamic>{'url': url, 'price': null}).toList()
            : <Map<String, dynamic>>[]);
"""
if anchor not in source:
    raise SystemExit("Could not locate inquiry reply data block.")
source = source.replace(anchor, replacement, 1)

anchor2 = """        if (status == 'answered' && ids is List && ids.isNotEmpty)
          FutureBuilder<List<Product>>(
"""
replacement2 = """        if (replyImages.isNotEmpty) ...[
          const SizedBox(height: 12),
          const Text(
            'الخيارات المتوفرة بالصور والأسعار',
            style: TextStyle(color: astroNavy, fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: replyImages.map((image) {
              final url = (image['url'] ?? '').toString();
              final price = double.tryParse('\${image['price'] ?? ''}');
              return SizedBox(
                width: 132,
                child: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    border: Border.all(color: const Color(0xFFE2ECF7)),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      ClipRRect(
                        borderRadius: BorderRadius.circular(9),
                        child: SizedBox(
                          height: 108,
                          child: AstroCachedImage(
                            imageUrl: url,
                            fit: BoxFit.contain,
                          ),
                        ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        price == null
                            ? 'السعر غير محدد'
                            : '\${price.toStringAsFixed(2)} د.ل',
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          color: astroBlue,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                    ],
                  ),
                ),
              );
            }).toList(),
          ),
        ],
        if (status == 'answered' && ids is List && ids.isNotEmpty)
          FutureBuilder<List<Product>>(
"""
if anchor2 not in source:
    raise SystemExit("Could not locate recommended products section.")
source = source.replace(anchor2, replacement2, 1)
dart.write_text(source, encoding="utf-8")

sql = Path("astro_mobile/supabase/product_inquiries.sql")
sql_source = sql.read_text(encoding="utf-8")
sql_anchor = """  admin_reply text,
  recommended_product_ids jsonb not null default '[]'::jsonb
"""
sql_replacement = """  admin_reply text,
  admin_image_urls jsonb not null default '[]'::jsonb
    check (jsonb_typeof(admin_image_urls) = 'array'),
  admin_image_items jsonb not null default '[]'::jsonb
    check (jsonb_typeof(admin_image_items) = 'array'),
  recommended_product_ids jsonb not null default '[]'::jsonb
"""
if sql_anchor not in sql_source:
    raise SystemExit("Could not locate product inquiry SQL schema block.")
sql_source = sql_source.replace(sql_anchor, sql_replacement, 1)
sql_source += """

-- Keep existing installations compatible when this script is re-run.
alter table public.product_inquiries
  add column if not exists admin_image_urls jsonb not null default '[]'::jsonb;
alter table public.product_inquiries
  add column if not exists admin_image_items jsonb not null default '[]'::jsonb;
"""
sql.write_text(sql_source, encoding="utf-8")
print("Patched inline inquiry replies to display each admin image and its Libyan dinar price.")
