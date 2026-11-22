from pathlib import Path
root=Path('astro_mobile')
src=Path('scripts/service_inquiries_screen.dart')
dst=root/'lib/screens/service_inquiries_screen.dart'
dst.parent.mkdir(parents=True,exist_ok=True)
dst.write_text(src.read_text(encoding='utf-8'),encoding='utf-8')
p=root/'lib/screens/contact_screen.dart'
s=p.read_text(encoding='utf-8')
if "import 'service_inquiries_screen.dart';" not in s:
 s=s.replace("import '../main.dart';","import '../main.dart';\nimport 'service_inquiries_screen.dart';",1)
anchor="                const Padding(padding: EdgeInsets.symmetric(horizontal: 4, vertical: 7), child: Text('موقع المتجر'"
if "خدمات الصيانة والبرمجة" not in s:
 i=s.find(anchor)
 if i<0: raise SystemExit('Contact screen insertion anchor missing')
 tile="""                _tile(Icons.build_circle_outlined,'خدمات الصيانة والبرمجة','استفسر عن الصيانة أو السوفتوير أو البرمجة عن بُعد',() => Navigator.push(context, MaterialPageRoute(builder: (_) => const ServiceInquiriesScreen()))),
                const SizedBox(height: 10),
"""
 s=s[:i]+tile+s[i:]
p.write_text(s,encoding='utf-8')
print('Service inquiry screen installed.')
