from pathlib import Path
import re

root = Path("astro_mobile")
main = root / "lib/main.dart"
source = main.read_text()
start = source.index("const Color astroNavy =")
end = source.index("const String supabaseUrl =")
palette = """const Color astroNavy = Color(0xFFEAF3FF);
const Color astroBlue = Color(0xFF087FF5);
const Color astroSky = Color(0xFF24D8FF);
const Color astroPurple = Color(0xFFB45CFF);
const Color astroBackground = Color(0xFF050B20);
const Color astroSurface = Color(0xFF0B1740);
const Color astroSurfaceAlt = Color(0xFF10245A);
const Color astroMuted = Color(0xFFB8C8E8);
const Color astroGold = astroBlue;

"""
source = source[:start] + palette + source[end:]
a = source.index("        theme: ThemeData(")
b = source.index("        home: const Directionality(", a)
theme = """        theme: ThemeData(
          useMaterial3: true,
          brightness: Brightness.dark,
          scaffoldBackgroundColor: astroBackground,
          colorScheme: ColorScheme.fromSeed(
            brightness: Brightness.dark,
            seedColor: astroBlue,
            primary: astroBlue,
            secondary: astroPurple,
            tertiary: astroSky,
            surface: astroSurface,
            error: const Color(0xFFFF647C),
          ),
          textTheme: ThemeData.dark().textTheme.apply(
            bodyColor: const Color(0xFFEAF3FF),
            displayColor: const Color(0xFFF7FAFF),
          ),
          appBarTheme: const AppBarTheme(
            backgroundColor: astroBackground,
            foregroundColor: astroNavy,
            elevation: 0,
            scrolledUnderElevation: 0,
            centerTitle: false,
            titleTextStyle: TextStyle(
              color: Color(0xFFF4F7FF),
              fontSize: 19,
              fontWeight: FontWeight.w900,
            ),
            iconTheme: IconThemeData(color: astroSky),
          ),
          cardTheme: CardThemeData(
            color: astroSurface,
            elevation: 8,
            shadowColor: Color(0x665B35B8),
            margin: EdgeInsets.zero,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(22),
              side: BorderSide(color: astroPurple.withOpacity(.58), width: 1.1),
            ),
          ),
          inputDecorationTheme: InputDecorationTheme(
            filled: true,
            fillColor: astroSurfaceAlt,
            contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 15),
            labelStyle: TextStyle(color: astroMuted),
            hintStyle: TextStyle(color: Color(0xFF879BC6)),
            prefixIconColor: astroSky,
            suffixIconColor: astroPurple,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(16),
              borderSide: BorderSide(color: astroPurple.withOpacity(.45)),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(16),
              borderSide: BorderSide(color: astroPurple.withOpacity(.35)),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(16),
              borderSide: BorderSide(color: astroSky, width: 1.8),
            ),
            errorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(16),
              borderSide: BorderSide(color: Color(0xFFFF647C)),
            ),
          ),
          elevatedButtonTheme: ElevatedButtonThemeData(
            style: ElevatedButton.styleFrom(
              backgroundColor: astroBlue,
              foregroundColor: Colors.white,
              elevation: 5,
              shadowColor: astroPurple.withOpacity(.35),
              minimumSize: Size(48, 50),
              padding: EdgeInsets.symmetric(horizontal: 20, vertical: 13),
              textStyle: TextStyle(fontWeight: FontWeight.w800, fontSize: 15),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            ),
          ),
          outlinedButtonTheme: OutlinedButtonThemeData(
            style: OutlinedButton.styleFrom(
              foregroundColor: astroSky,
              minimumSize: Size(44, 48),
              side: BorderSide(color: astroPurple.withOpacity(.7)),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
            ),
          ),
          snackBarTheme: SnackBarThemeData(
            behavior: SnackBarBehavior.floating,
            backgroundColor: astroSurfaceAlt,
            contentTextStyle: TextStyle(color: Color(0xFFF4F7FF)),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
              side: BorderSide(color: astroPurple.withOpacity(.55)),
            ),
          ),
          dividerTheme: DividerThemeData(
            color: astroPurple.withOpacity(.32),
            thickness: 1,
            space: 1,
          ),
        ),
"""
source = source[:a] + theme + source[b:]
main.write_text(source)

pale_fills = [
    "0xFFF7FAFE", "0xFFF8FAFD", "0xFFF5F9FE", "0xFFF2F7FD",
    "0xFFF2F6FC", "0xFFF3F6FC", "0xFFF1F4FA", "0xFFF1F6FD",
    "0xFFEAF4FF", "0xFFE6F4FF", "0xFFE8F3FF", "0xFFE3F0FF",
]
text_colors = {
    "Colors.black87": "Colors.white",
    "Colors.black54": "Colors.white70",
    "Colors.black45": "Colors.white60",
    "Colors.black38": "Colors.white54",
    "Colors.black26": "Colors.white38",
    "Color(0xFF718096)": "Color(0xFFB8C8E8)",
    "Color(0xFF718198)": "Color(0xFFB8C8E8)",
    "Color(0xFF8492A3)": "Color(0xFFAFC0E4)",
    "Color(0xFF8A98A9)": "Color(0xFFAFC0E4)",
    "Color(0xFF65758B)": "Color(0xFFB8C8E8)",
    "Color(0xFF64748B)": "Color(0xFFB8C8E8)",
    "Color(0xFF94A3B8)": "Color(0xFF9DB0D8)",
}
for path in (root / "lib/screens").glob("*.dart"):
    text = path.read_text()
    text = re.sub(
        r"color:\s*(?:const\s+)?Colors\.white,(?=\s*(?:border:|borderRadius:|boxShadow:|shape:|elevation:))",
        "color: astroSurface,", text
    )
    text = text.replace("BoxDecoration(color: Colors.white,", "BoxDecoration(color: astroSurface,")
    for fill in pale_fills:
        text = text.replace(f"const Color({fill})", "astroSurfaceAlt")
        text = text.replace(f"Color({fill})", "astroSurfaceAlt")
    text = re.sub(
        r"Border\.all\(color:\s*(?:const\s+)?Color\(0xFFE[0-9A-Fa-f]{6}\)\)",
        "Border.all(color: astroPurple.withOpacity(.48), width: 1.0)", text
    )
    for old, new in text_colors.items():
        text = text.replace(old, new)
    text = text.replace("const astroSurfaceAlt", "astroSurfaceAlt")
    text = text.replace("const astroSurface", "astroSurface")
    path.write_text(text)

print("ASTRO neon-blue/purple theme applied to the app and all screen surfaces.")

# Harmonize category cards with the dark neon identity. The first neon build
# still left the category tiles with pastel/white surfaces; replace those
# surfaces while preserving category images, labels, navigation and layout.
home = root / "lib/screens/home_screen.dart"
h = home.read_text(encoding="utf-8")

old_palette = """                      final palette = const [
                        Color(0xFFDCEEFF), Color(0xFFDDF5E8), Color(0xFFEFE2FF),
                        Color(0xFFFFE8D5), Color(0xFFFFE1EA), Color(0xFFE3EAFF),
                        Color(0xFFDDF5F7), Color(0xFFFFF1D9),
                      ];
"""
if old_palette in h:
    h = h.replace(old_palette, "", 1)
old_carousel = """                              decoration: BoxDecoration(
                                color: palette[index % palette.length],
                                borderRadius: BorderRadius.circular(20),
                                border: Border.all(color: const Color(0xFFD5E4F3)),
                              ),
"""
new_carousel = """                              decoration: BoxDecoration(
                                gradient: const LinearGradient(
                                  begin: Alignment.topLeft,
                                  end: Alignment.bottomRight,
                                  colors: [astroSurfaceAlt, astroSurface, Color(0xFF17265B)],
                                ),
                                borderRadius: BorderRadius.circular(20),
                                border: Border.all(color: astroPurple.withOpacity(.72), width: 1.15),
                                boxShadow: [
                                  BoxShadow(color: astroBlue.withOpacity(.16), blurRadius: 16, offset: const Offset(0, 5)),
                                ],
                              ),
"""
if old_carousel in h:
    h = h.replace(old_carousel, new_carousel, 1)
elif "colors: [astroSurfaceAlt, astroSurface, Color(0xFF17265B)]" not in h:
    raise SystemExit("Home category carousel surface anchor mismatch")

old_grid = """                              gradient: const LinearGradient(
                                begin: Alignment.topRight,
                                end: Alignment.bottomLeft,
                                colors: [Colors.white, Color(0xFFF0F7FF)],
                              ),
                              borderRadius: BorderRadius.circular(20),
                              border: Border.all(
                                color: const Color(0xFFDCE9F6),
                                width: 1.1,
                              ),
                              boxShadow: [
                                BoxShadow(
                                  color: astroNavy.withOpacity(.055),
                                  blurRadius: 13,
                                  offset: const Offset(0, 5),
                                ),
                              ],
"""
new_grid = """                              gradient: const LinearGradient(
                                begin: Alignment.topRight,
                                end: Alignment.bottomLeft,
                                colors: [Color(0xFF14275B), astroSurface, Color(0xFF080F2B)],
                              ),
                              borderRadius: BorderRadius.circular(20),
                              border: Border.all(
                                color: astroPurple.withOpacity(.78),
                                width: 1.25,
                              ),
                              boxShadow: [
                                BoxShadow(
                                  color: astroBlue.withOpacity(.18),
                                  blurRadius: 18,
                                  offset: const Offset(0, 6),
                                ),
                              ],
"""
if old_grid in h:
    h = h.replace(old_grid, new_grid, 1)
elif "colors: [Color(0xFF14275B), astroSurface, Color(0xFF080F2B)]" not in h:
    raise SystemExit("All-categories card surface anchor mismatch")

old_icon = """                                    gradient: const LinearGradient(
                                      colors: [astroSurfaceAlt, Color(0xFFDCEEFF)],
                                      begin: Alignment.topLeft,
                                      end: Alignment.bottomRight,
                                    ),
                                    borderRadius: BorderRadius.circular(19),
"""
new_icon = """                                    gradient: const LinearGradient(
                                      colors: [Color(0xFF244A91), Color(0xFF17204F), Color(0xFF552B83)],
                                      begin: Alignment.topLeft,
                                      end: Alignment.bottomRight,
                                    ),
                                    borderRadius: BorderRadius.circular(19),
                                    border: Border.all(color: astroSky.withOpacity(.62), width: 1.0),
"""
if old_icon in h:
    h = h.replace(old_icon, new_icon, 1)
elif "Color(0xFF552B83)" not in h:
    raise SystemExit("Category icon frame anchor mismatch")

old_badge = """                                    color: Colors.white.withOpacity(.9),
                                    borderRadius: BorderRadius.circular(20),
"""
new_badge = """                                    color: const Color(0xFF0D1A42).withOpacity(.94),
                                    border: Border.all(color: astroPurple.withOpacity(.48)),
                                    borderRadius: BorderRadius.circular(20),
"""
if old_badge in h:
    h = h.replace(old_badge, new_badge, 1)
elif "Color(0xFF0D1A42).withOpacity(.94)" not in h:
    raise SystemExit("Category sublabel surface anchor mismatch")

h = h.replace(
    "color: const Color(0xFF6B7F93),",
    "color: const Color(0xFFB8C8E8),",
    1,
)
home.write_text(h, encoding="utf-8")
print("Category cards and image frames now use coordinated neon navy/blue/purple surfaces.")
