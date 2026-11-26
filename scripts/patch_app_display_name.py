from pathlib import Path
import re

manifest = Path("astro_mobile/android/app/src/main/AndroidManifest.xml")
if not manifest.is_file():
    raise SystemExit(f"Android manifest not found: {manifest}")

source = manifest.read_text(encoding="utf-8")
application = re.search(r"<application\b[^>]*>", source, flags=re.DOTALL)
if application is None:
    raise SystemExit("Could not find the Android <application> element.")

tag = application.group(0)
if re.search(r"\bandroid:label\s*=", tag):
    updated_tag = re.sub(
        r'android:label\s*=\s*"[^"]*"',
        'android:label="Astro Mobile"',
        tag,
        count=1,
    )
else:
    updated_tag = tag[:-1] + ' android:label="Astro Mobile">'

source = source[:application.start()] + updated_tag + source[application.end():]
manifest.write_text(source, encoding="utf-8")
print("Android launcher name set to Astro Mobile.")
