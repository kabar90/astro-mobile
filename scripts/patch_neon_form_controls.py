from pathlib import Path

ROOT = Path("astro_mobile/lib/screens")

def patch_file(name, replacements):
    path = ROOT / name
    source = path.read_text(encoding="utf-8")
    for old, new, label in replacements:
        count = source.count(old)
        if count:
            source = source.replace(old, new, 1)
            print(f"{name}: {label}")
        elif new not in source:
            print(f"NOTE: {name}: anchor not present for {label}")
    path.write_text(source, encoding="utf-8")

patch_file("product_detail_screen.dart", [
    ("color: const Color(0xFFE7F3FF),", "color: astroSurfaceAlt,", "dark price and stock panel"),
    ("color: const Color(0xFFFFF7E5),", "color: astroSurfaceAlt,", "dark rewards panel"),
    ("border: Border.all(color: const Color(0xFFF1E1B8)),", "border: Border.all(color: astroPurple.withOpacity(.58)),", "rewards neon border"),
    ("color: Color(0xFFD69A22),", "color: astroSky,", "rewards icon contrast"),
    ("color: Color(0xFF8A6416),", "color: astroNavy,", "rewards text contrast"),
    (": const Color(0xFFFAFBFD),", ": astroSurface,", "dark unselected color chips"),
    (": const Color(0xFFDDE5EF),", ": astroPurple.withOpacity(.62),", "purple color-chip borders"),
    ("border: Border.all(color: const Color(0xFFE1EAF5)),", "border: Border.all(color: astroSky.withOpacity(.58)),", "quantity selector neon border"),
    ("color: enabled ? Colors.white : const Color(0xFFE8EDF4),", "color: enabled ? astroSurface : const Color(0xFF263765),", "dark quantity buttons"),
    ("color: enabled ? astroBlue : Colors.white38", "color: enabled ? astroSky : Colors.white38", "quantity button icon"),
    ("color: Colors.white.withOpacity(.94),", "color: astroSurfaceAlt.withOpacity(.96),", "dark gallery arrows"),
    ("child: Icon(icon, color: astroNavy, size: 25),", "child: Icon(icon, color: astroSky, size: 25),", "gallery arrow icon"),
])

patch_file("checkout_screen.dart", [
    ("fillColor: Colors.white,", "fillColor: astroSurfaceAlt,", "dark search and customer fields"),
    ("border: Border.all(color: const Color(0xFFE2E8F0)),", "border: Border.all(color: astroPurple.withOpacity(.62)),", "city list neon border"),
    ("title: Text(city['city_name'].toString(), style: const TextStyle(fontWeight: FontWeight.w700)),",
     "title: Text(city['city_name'].toString(), style: const TextStyle(color: astroNavy, fontWeight: FontWeight.w800)),", "city text contrast"),
    ("Text('\${(city['delivery_fee'] as num).toStringAsFixed(2)} د.ل'),",
     "Text('\${(city['delivery_fee'] as num).toStringAsFixed(2)} د.ل', style: const TextStyle(color: astroSky, fontWeight: FontWeight.w800)),", "city fee contrast"),
    ("separatorBuilder: (_, __) => const Divider(height: 1, indent: 14, endIndent: 14),",
     "separatorBuilder: (_, __) => Divider(height: 1, indent: 14, endIndent: 14, color: astroPurple.withOpacity(.28)),", "city list separators"),
    ("border: Border.all(color: const Color(0xFFE1EAF5)),", "border: Border.all(color: astroPurple.withOpacity(.58)),", "checkout card borders"),
])

patch_file("account_screen.dart", [
    ("style: ElevatedButton.styleFrom(backgroundColor: astroNavy, foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(13))),",
     "style: ElevatedButton.styleFrom(backgroundColor: astroBlue, foregroundColor: Colors.white, elevation: 5, shadowColor: astroPurple.withOpacity(.35), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(13))),", "login button contrast"),
])

patch_file("bank_transfer_screen.dart", [
    ("color: Colors.grey, fontSize: 13,", "color: astroMuted, fontSize: 13,", "bank field label contrast"),
    ("fontWeight: FontWeight.bold, fontSize: 15,", "color: astroNavy, fontWeight: FontWeight.bold, fontSize: 15,", "bank field value contrast"),
    ("color: astroNavy,\n            ),", "color: astroSky,\n            ),", "copy icon contrast"),
    ("size: 48, color: astroNavy)", "size: 48, color: astroSky)", "bank header icon"),
    ("backgroundColor: astroNavy,\n                          foregroundColor: Colors.white,", "backgroundColor: astroBlue,\n                          foregroundColor: Colors.white,", "confirm transfer button"),
])

patch_file("home_screen.dart", [
    ("backgroundColor: Colors.white,\n      shape: const RoundedRectangleBorder(\n        borderRadius: BorderRadius.vertical(top: Radius.circular(22)),",
     "backgroundColor: astroSurface,\n      shape: const RoundedRectangleBorder(\n        borderRadius: BorderRadius.vertical(top: Radius.circular(22)),", "dark filter sheet"),
    ("title: const Text('الكل'),", "title: const Text('الكل', style: TextStyle(color: astroNavy, fontWeight: FontWeight.w700)),", "filter option text"),
    ("title: Text(item.name),", "title: Text(item.name, style: const TextStyle(color: astroNavy, fontWeight: FontWeight.w700)),", "subcategory text"),
    ("foregroundColor: astroNavy,\n                        backgroundColor: Colors.white,\n                        side: const BorderSide(color: Color(0xFFE0EAF5)),",
     "foregroundColor: astroSky,\n                        backgroundColor: astroSurface,\n                        side: BorderSide(color: astroPurple.withOpacity(.72), width: 1.1),", "filter button"),
    ("foregroundColor: astroNavy,\n                    backgroundColor: Colors.white,\n                    side: const BorderSide(color: Color(0xFFE0EAF5)),",
     "foregroundColor: astroSky,\n                    backgroundColor: astroSurface,\n                    side: BorderSide(color: astroPurple.withOpacity(.72), width: 1.1),", "change category button"),
    ("color: astroSurface,\n                          borderRadius: BorderRadius.circular(16),\n                          border: Border.all(color: const Color(0xFFE0EAF5)),",
     "color: astroSurface,\n                          borderRadius: BorderRadius.circular(16),\n                          border: Border.all(color: astroPurple.withOpacity(.58)),", "sort control border"),
])

print("ASTRO neon form, filter, product-detail and payment controls patch completed.")
