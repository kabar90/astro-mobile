from pathlib import Path
root=Path('astro_mobile')
src=Path('scripts/service_inquiries_screen.dart')
dst=root/'lib/screens/service_inquiries_screen.dart'
dst.parent.mkdir(parents=True,exist_ok=True)
dst.write_text(src.read_text(encoding='utf-8'),encoding='utf-8')
p=root/'lib/screens/home_screen.dart'
s=p.read_text(encoding='utf-8')
if "import 'service_inquiries_screen.dart';" not in s:
 s=s.replace("import '../main.dart';","import '../main.dart';\nimport 'service_inquiries_screen.dart';",1)
anchor="""          if (selectedRoot != null &&
              (selectedRoot.name.contains('لوحي') || selectedRoot.name.contains('تابلت'))) ...[
            SliverToBoxAdapter(child: _tabletCategoryBanner()),
          ],"""
replacement=anchor+"""
          if (selectedRoot != null &&
              (selectedRoot.name.contains('صيانة') || selectedRoot.name.toLowerCase().contains('soft'))) ...[
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
                child: Card(
                  elevation: 0,
                  color: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(18),
                    side: const BorderSide(color: Color(0xFFE0EAF5)),
                  ),
                  child: ListTile(
                    leading: const CircleAvatar(
                      backgroundColor: Color(0xFFEAF4FF),
                      child: Icon(Icons.build_circle_outlined, color: astroBlue),
                    ),
                    title: const Text('خدمات الصيانة والبرمجة', style: TextStyle(color: astroNavy, fontWeight: FontWeight.w900)),
                    subtitle: const Text('استفسر عن الصيانة أو السوفتوير أو البرمجة عن بُعد'),
                    trailing: const Icon(Icons.arrow_forward_ios_rounded, size: 16, color: astroBlue),
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ServiceInquiriesScreen())),
                  ),
                ),
              ),
            ),
          ],"""
if "خدمات الصيانة والبرمجة" not in s:
 if anchor not in s: raise SystemExit('Category section anchor missing')
 s=s.replace(anchor,replacement,1)
p.write_text(s,encoding='utf-8')
print('Service inquiries added inside maintenance/software category.')
