from pathlib import Path

home = Path('astro_mobile/lib/screens/home_screen.dart')
s = home.read_text(encoding='utf-8')

# Compact featured offers to match the latest-products carousel footprint.
replacements = [
    ('''                                child: SizedBox(
                                  height: 370,
                                  child: ListView.separated(''',
     '''                                child: SizedBox(
                                  height: 258,
                                  child: ListView.separated(''',
     'carousel height'),
    ('''                                    itemBuilder: (context, index) => SizedBox(
                                      width: MediaQuery.of(context).size.width * 0.86,
                                      child: featuredOfferSections[index],
                                    ),''',
     '''                                    itemBuilder: (context, index) => SizedBox(
                                      width: 174,
                                      height: 258,
                                      child: featuredOfferSections[index],
                                    ),''',
     'carousel width'),
    ('''                                                SizedBox(
                                                  height: 148,
                                                  child: Stack(''',
     '''                                                SizedBox(
                                                  height: 70,
                                                  child: Stack(''',
     'bundle cover height'),
    ('''                                          childAspectRatio: 0.90,
                                        ),
                                        itemBuilder: (context, index) {''',
     '''                                          childAspectRatio: 1.0,
                                        ),
                                        itemBuilder: (context, index) {''',
     'bundle tile ratio'),
    ('''                                                SizedBox(
                                                  height: 46,
                                                  child: ElevatedButton(''',
     '''                                                SizedBox(
                                                  height: 34,
                                                  child: ElevatedButton(''',
     'bundle details button height'),
    ('''                                                      minimumSize: const Size(double.infinity, 46),''',
     '''                                                      minimumSize: const Size(double.infinity, 34),''',
     'bundle details button minimum'),
    ('''                                                  aspectRatio: 1.65,''',
     '''                                                  aspectRatio: 1.8,''',
     'regular offer cover ratio'),
    ('''                                              const SizedBox(height: 12),
                                              Row(
                                                children: [
                                                  Expanded(
                                                    child: Text(offerName, maxLines: 2,''',
     '''                                              const SizedBox(height: 6),
                                              Row(
                                                children: [
                                                  Expanded(
                                                    child: Text(offerName, maxLines: 2,''',
     'regular offer title spacing'),
]
for old, new, label in replacements:
    if old in s:
        s = s.replace(old, new, 1)
    elif new not in s:
        raise SystemExit(f'Missing expected source anchor: {label}')

s = s.replace(
    '''                                        return Container(
                                          margin: const EdgeInsets.fromLTRB(12, 2, 12, 14),
                                          padding: const EdgeInsets.all(10),''',
    '''                                        return Container(
                                          margin: const EdgeInsets.fromLTRB(2, 2, 2, 4),
                                          padding: const EdgeInsets.all(7),''',
    1,
)
s = s.replace(
    '''                                              const SizedBox(height: 10),
                                              SizedBox(
                                                height: 46,''',
    '''                                              const SizedBox(height: 6),
                                              SizedBox(
                                                height: 38,''',
    1,
)
s = s.replace(
    '''                                                    minimumSize: const Size(double.infinity, 42),''',
    '''                                                    minimumSize: const Size(double.infinity, 36),''',
    1,
)
s = s.replace(
    '''                                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
                                  child: Column(''',
    '''                                  padding: const EdgeInsets.fromLTRB(4, 2, 4, 4),
                                  child: Column(''',
    1,
)
s = s.replace(
    '''                                              margin: const EdgeInsets.fromLTRB(10, 0, 10, 6),
                                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),''',
    '''                                              margin: const EdgeInsets.fromLTRB(2, 0, 2, 4),
                                              padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 3),''',
    1,
)
home.write_text(s, encoding='utf-8')
print('Featured home offers resized to compact 174x258 cards; offer data, countdowns, product details and bundle checkout preserved.')
