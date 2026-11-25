from pathlib import Path

ROOT = Path("astro_mobile/lib/screens")

def edit(name, replacements):
    path = ROOT / name
    source = path.read_text(encoding="utf-8")
    for old, new, label in replacements:
        if old not in source:
            if new in source:
                continue
            raise SystemExit(f"{name}: could not find anchor: {label}")
        source = source.replace(old, new, 1)
    path.write_text(source, encoding="utf-8")
    print(f"Updated {name}")

# Product details: replace the remaining pale panels and controls with dark
# navy surfaces, cyan text accents and purple/cyan neon borders.
edit("product_detail_screen.dart", [
    ("border: Border.all(color: const Color(0xFFE4ECF5)),",
     "border: Border.all(color: astroPurple.withOpacity(.62), width: 1.1),", "gallery border"),
    ("color: const Color(0xFFE7F3FF),", "color: astroSurfaceAlt,", "price/stock panel"),
    ("color: const Color(0xFFFFF7E5),", "color: astroSurfaceAlt,", "rewards panel"),
    ("border: Border.all(color: const Color(0xFFF1E1B8)),",
     "border: Border.all(color: astroPurple.withOpacity(.58)),", "rewards border"),
    ("color: Color(0xFFD69A22),", "color: astroSky,", "rewards icon"),
    ("color: Color(0xFF8A6416),", "color: astroNavy,", "rewards text"),
    (": const Color(0xFFFAFBFD),", ": astroSurface,", "unselected color chip"),
    (": const Color(0xFFDDE5EF),", ": astroPurple.withOpacity(.62),", "unselected color border"),
    ("color: const Color(0xFFF5F9FE),", "color: astroSurfaceAlt,", "quantity container"),
    ("border: Border.all(color: const Color(0xFFE1EAF5)),",
     "border: Border.all(color: astroSky.withOpacity(.58)),", "quantity border"),
    ("color: enabled ? Colors.white : const Color(0xFFE8EDF4),",
     "color: enabled ? astroSurface : const Color(0xFF263765),", "quantity buttons"),
    ("color: enabled ? astroBlue : Colors.white38",
     "color: enabled ? astroSky : Colors.white38", "quantity button icon"),
    ("color: Colors.white.withOpacity(.94),", "color: astroSurfaceAlt.withOpacity(.96),", "gallery arrows"),
    ("child: Icon(icon, color: astroNavy, size: 25),", "child: Icon(icon, color: astroSky, size: 25),", "gallery arrow icon"),
])

# Checkout: dark input fills, visible labels and neon outlines; keep all
# delivery/payment behavior untouched.
edit("checkout_screen.dart", [
    ("fillColor: Colors.white,", "fillColor: astroSurfaceAlt,", "city search fill"),
    ("border: Border.all(color: const Color(0xFFE2E8F0)),",
     "border: Border.all(color: astroPurple.withOpacity(.62)),", "city list border"),
    ("selectedTileColor: astroSurfaceAlt,",
     "selectedTileColor: const Color(0xFF1A3472),", "selected city row"),
    ("title: Text(city['city_name'].toString(), style: const TextStyle(fontWeight: FontWeight.w700)),",
     "title: Text(city['city_name'].toString(), style: const TextStyle(color: astroNavy, fontWeight: FontWeight.w800)),", "city name"),
    ("Text('${(city['delivery_fee'] as num).toStringAsFixed(2)} د.ل'),",
     "Text('${(city['delivery_fee'] as num).toStringAsFixed(2)} د.ل', style: const TextStyle(color: astroSky, fontWeight: FontWeight.w800)),", "city fee"),
    ("separatorBuilder: (_, __) => const Divider(height: 1, indent: 14, endIndent: 14),",
     "separatorBuilder: (_, __) => Divider(height: 1, indent: 14, endIndent: 14, color: astroPurple.withOpacity(.28)),", "city divider"),
    ("border: Border.all(color: const Color(0xFFE1EAF5)),",
     "border: Border.all(color: astroPurple.withOpacity(.58)),", "checkout summary border"),
    ("decoration: BoxDecoration(color: astroSurface, borderRadius: BorderRadius.circular(20), border: Border.all(color: const Color(0xFFE1EAF5)),",
     "decoration: BoxDecoration(color: astroSurface, borderRadius: BorderRadius.circular(20), border: Border.all(color: astroPurple.withOpacity(.58)),", "section card border"),
    ("          fillColor: Colors.white,\n          border: OutlineInputBorder(\n            borderRadius: BorderRadius.circular(14),\n          ),",
     "          fillColor: astroSurfaceAlt,\n          labelStyle: const TextStyle(color: astroMuted),\n          hintStyle: const TextStyle(color: Color(0xFF91A5D0)),\n          prefixIconColor: astroSky,\n          style: const TextStyle(color: astroNavy, fontWeight: FontWeight.w600),\n          enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: BorderSide(color: astroPurple.withOpacity(.48))),\n          focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: astroSky, width: 1.7)),\n          border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),", "customer input decoration"),
])

# Login: astroNavy is now a pale foreground color, so it must not be used as
# the filled CTA background (this caused the white-on-white login button).
edit("account_screen.dart", [
    ("style: ElevatedButton.styleFrom(backgroundColor: astroNavy, foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(13))),",
     "style: ElevatedButton.styleFrom(backgroundColor: astroBlue, foregroundColor: Colors.white, elevation: 5, shadowColor: astroPurple.withOpacity(.35), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(13))),", "login button"),
])

# Bank transfer: improve metadata contrast and use the same blue CTA as the
# rest of the app; upload button inherits the neon outlined-button theme.
edit("bank_transfer_screen.dart", [
    ("color: Colors.grey, fontSize: 13,", "color: astroMuted, fontSize: 13,", "bank field label"),
    ("fontWeight: FontWeight.bold, fontSize: 15,", "color: astroNavy, fontWeight: FontWeight.bold, fontSize: 15,", "bank field value"),
    ("color: astroNavy,\n            ),", "color: astroSky,\n            ),", "copy icon"),
    ("size: 48, color: astroNavy)", "size: 48, color: astroSky)", "bank header icon"),
    ("backgroundColor: astroNavy,\n                          foregroundColor: Colors.white,",
     "backgroundColor: astroBlue,\n                          foregroundColor: Colors.white,", "confirm transfer button"),
])

# Category filter: dark bottom sheet and dark filter/sort controls instead of
# white pills on a navy screen.
edit("home_screen.dart", [
    ("backgroundColor: Colors.white,\n      shape: const RoundedRectangleBorder(\n        borderRadius: BorderRadius.vertical(top: Radius.circular(22)),",
     "backgroundColor: astroSurface,\n      shape: const RoundedRectangleBorder(\n        borderRadius: BorderRadius.vertical(top: Radius.circular(22)),", "filter sheet"),
    ("const Text('تصفية حسب القسم الفرعي', style: TextStyle(color: astroNavy, fontSize: 17, fontWeight: FontWeight.w900)),",
     "const Text('تصفية حسب القسم الفرعي', style: TextStyle(color: astroNavy, fontSize: 17, fontWeight: FontWeight.w900)),", "filter title"),
    ("title: const Text('الكل'),", "title: const Text('الكل', style: TextStyle(color: astroNavy, fontWeight: FontWeight.w700)),", "all filter option"),
    ("title: Text(item.name),", "title: Text(item.name, style: const TextStyle(color: astroNavy, fontWeight: FontWeight.w700)),", "subcategory filter option"),
    ("foregroundColor: astroNavy,\n                        backgroundColor: Colors.white,\n                        side: const BorderSide(color: Color(0xFFE0EAF5)),",
     "foregroundColor: astroSky,\n                        backgroundColor: astroSurface,\n                        side: BorderSide(color: astroPurple.withOpacity(.72), width: 1.1),", "filter button"),
    ("foregroundColor: astroNavy,\n                    backgroundColor: Colors.white,\n                    side: const BorderSide(color: Color(0xFFE0EAF5)),",
     "foregroundColor: astroSky,\n                    backgroundColor: astroSurface,\n                    side: BorderSide(color: astroPurple.withOpacity(.72), width: 1.1),", "change category button"),
    ("color: astroSurface,\n                          borderRadius: BorderRadius.circular(16),\n                          border: Border.all(color: const Color(0xFFE0EAF5)),",
     "color: astroSurface,\n                          borderRadius: BorderRadius.circular(16),\n                          border: Border.all(color: astroPurple.withOpacity(.58)),", "sort control"),
athlib import Path

ROOT = Path("astro_mobile/lib/screens")

def edit(name, replacements):
    path = ROOT / name
    source = path.read_text(encoding="utf-8")
    for old, new, label in replacements:
        if old not in source:
            if new in source:
                continue
            raise SystemExit(f"{name}: could not find anchor: {label}")
        source = source.replace(old, new, 1)
    path.write_text(source, encoding="utf-8")
    print(f"Updated {name}")

# Product details: replace the remaining pale panels and controls with dark
# navy surfaces, cyan text accents and purple/cyan neon borders.
edit("product_detail_screen.dart", [
    ("border: Border.all(color: const Color(0xFFE4ECF5)),",
     "border: Border.all(color: astroPurple.withOpacity(.62), width: 1.1),", "gallery border"),
    ("color: const Color(0xFFE7F3FF),", "color: astroSurfaceAlt,", "price/stock panel"),
    ("color: const Color(0xFFFFF7E5),", "color: astroSurfaceAlt,", "rewards panel"),
    ("border: Border.all(color: const Color(0xFFF1E1B8)),",
     "border: Border.all(color: astroPurple.withOpacity(.58)),", "rewards border"),
    ("color: const Color(0xFFD69A22),", "color: astroSky,", "rewards icon"),
    ("color: const Color(0xFF8A6416),", "color: astroNavy,", "rewards text"),
    (": const Color(0xFFFAFBFD),", ": astroSurface,", "unselected color chip"),
    (": const Color(0xFFDDE5EF),", ": astroPurple.withOpacity(.62),", "unselected color border"),
    ("color: const Color(0xFFF5F9FE),", "color: astroSurfaceAlt,", "quantity container"),
    ("border: Border.all(color: const Color(0xFFE1EAF5)),",
     "border: Border.all(color: astroSky.withOpacity(.58)),", "quantity border"),
    ("color: enabled ? Colors.white : const Color(0xFFE8EDF4),",
     "color: enabled ? astroSurface : const Color(0xFF263765),", "quantity buttons"),
    ("color: enabled ? astroBlue : Colors.white38",
     "color: enabled ? astroSky : Colors.white38", "quantity button icon"),
    ("color: Colors.white.withOpacity(.94),", "color: astroSurfaceAlt.withOpacity(.96),", "gallery arrows"),
    ("child: Icon(icon, color: astroNavy, size: 25),", "child: Icon(icon, color: astroSky, size: 25),", "gallery arrow icon"),
])

# Checkout: dark input fills, visible labels and neon outlines; keep all
# delivery/payment behavior untouched.
edit("checkout_screen.dart", [
    ("fillColor: Colors.white,", "fillColor: astroSurfaceAlt,", "city search fill"),
    ("border: Border.all(color: const Color(0xFFE2E8F0)),",
     "border: Border.all(color: astroPurple.withOpacity(.62)),", "city list border"),
    ("selectedTileColor: astroSurfaceAlt,",
     "selectedTileColor: const Color(0xFF1A3472),", "selected city row"),
    ("title: Text(city['city_name'].toString(), style: const TextStyle(fontWeight: FontWeight.w700)),",
     "title: Text(city['city_name'].toString(), style: const TextStyle(color: astroNavy, fontWeight: FontWeight.w800)),", "city name"),
    ("Text('${(city['delivery_fee'] as num).toStringAsFixed(2)} د.ل'),",
     "Text('${(city['delivery_fee'] as num).toStringAsFixed(2)} د.ل', style: const TextStyle(color: astroSky, fontWeight: FontWeight.w800)),", "city fee"),
    ("separatorBuilder: (_, __) => const Divider(height: 1, indent: 14, endIndent: 14),",
     "separatorBuilder: (_, __) => Divider(height: 1, indent: 14, endIndent: 14, color: astroPurple.withOpacity(.28)),", "city divider"),
    ("border: Border.all(color: const Color(0xFFE1EAF5)),",
     "border: Border.all(color: astroPurple.withOpacity(.58)),", "checkout summary border"),
    ("decoration: BoxDecoration(color: astroSurface, borderRadius: BorderRadius.circular(20), border: Border.all(color: const Color(0xFFE1EAF5)),",
     "decoration: BoxDecoration(color: astroSurface, borderRadius: BorderRadius.circular(20), border: Border.all(color: astroPurple.withOpacity(.58)),", "section card border"),
    ("          fillColor: Colors.white,\n          border: OutlineInputBorder(\n            borderRadius: BorderRadius.circular(14),\n          ),",
     "          fillColor: astroSurfaceAlt,\n          labelStyle: const TextStyle(color: astroMuted),\n          hintStyle: const TextStyle(color: Color(0xFF91A5D0)),\n          prefixIconColor: astroSky,\n          style: const TextStyle(color: astroNavy, fontWeight: FontWeight.w600),\n          enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: BorderSide(color: astroPurple.withOpacity(.48))),\n          focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: astroSky, width: 1.7)),\n          border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),", "customer input decoration"),
])

# Login: astroNavy is now a pale foreground color, so it must not be used as
# the filled CTA background (this caused the white-on-white login button).
edit("account_screen.dart", [
    ("style: ElevatedButton.styleFrom(backgroundColor: astroNavy, foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(13))),",
     "style: ElevatedButton.styleFrom(backgroundColor: astroBlue, foregroundColor: Colors.white, elevation: 5, shadowColor: astroPurple.withOpacity(.35), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(13))),", "login button"),
])

# Bank transfer: improve metadata contrast and use the same blue CTA as the
# rest of the app; upload button inherits the neon outlined-button theme.
edit("bank_transfer_screen.dart", [
    ("color: Colors.grey, fontSize: 13,", "color: astroMuted, fontSize: 13,", "bank field label"),
    ("fontWeight: FontWeight.bold, fontSize: 15,", "color: astroNavy, fontWeight: FontWeight.bold, fontSize: 15,", "bank field value"),
    ("color: astroNavy,\n            ),", "color: astroSky,\n            ),", "copy icon"),
    ("size: 48, color: astroNavy)", "size: 48, color: astroSky)", "bank header icon"),
    ("backgroundColor: astroNavy,\n                          foregroundColor: Colors.white,",
     "backgroundColor: astroBlue,\n                          foregroundColor: Colors.white,", "confirm transfer button"),
])

# Category filter: dark bottom sheet and dark filter/sort controls instead of
# white pills on a navy screen.
edit("home_screen.dart", [
    ("backgroundColor: Colors.white,\n      shape: const RoundedRectangleBorder(\n        borderRadius: BorderRadius.vertical(top: Radius.circular(22)),",
     "backgroundColor: astroSurface,\n      shape: const RoundedRectangleBorder(\n        borderRadius: BorderRadius.vertical(top: Radius.circular(22)),", "filter sheet"),
    ("const Text('تصفية حسب القسم الفرعي', style: TextStyle(color: astroNavy, fontSize: 17, fontWeight: FontWeight.w900)),",
     "const Text('تصفية حسب القسم الفرعي', style: TextStyle(color: astroNavy, fontSize: 17, fontWeight: FontWeight.w900)),", "filter title"),
    ("title: const Text('الكل'),", "title: const Text('الكل', style: TextStyle(color: astroNavy, fontWeight: FontWeight.w700)),", "all filter option"),
    ("title: Text(item.name),", "title: Text(item.name, style: const TextStyle(color: astroNavy, fontWeight: FontWeight.w700)),", "subcategory filter option"),
    ("foregroundColor: astroNavy,\n                        backgroundColor: Colors.white,\n                        side: const BorderSide(color: Color(0xFFE0EAF5)),",
     "foregroundColor: astroSky,\n                        backgroundColor: astroSurface,\n                        side: BorderSide(color: astroPurple.withOpacity(.72), width: 1.1),", "filter button"),
    ("foregroundColor: astroNavy,\n                    backgroundColor: Colors.white,\n                    side: const BorderSide(color: Color(0xFFE0EAF5)),",
     "foregroundColor: astroSky,\n                    backgroundColor: astroSurface,\n                    side: BorderSide(color: astroPurple.withOpacity(.72), width: 1.1),", "change category button"),
    ("color: Colors.white,\n                          borderRadius: BorderRadius.circular(16),\n                          border: Border.all(color: const Color(0xFFE0EAF5)),",
     "color: astroSurface,\n                          borderRadius: BorderRadius.circular(16),\n                          border: Border.all(color: astroPurple.withOpacity(.58)),", "sort control"),
])

print("Remaining low-contrast form and filter controls updated.")
