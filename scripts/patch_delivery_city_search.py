from pathlib import Path
p = Path('astro_mobile/lib/screens/checkout_screen.dart')
s = p.read_text()
if 'ASTRO_DELIVERY_CITY_SEARCH_PATCH' in s:
    print('Delivery city search patch already applied.')
    raise SystemExit(0)
old = """  String? _selectedCityId;

  Map<String, dynamic>? get _selectedCity {"""
new = """  String? _selectedCityId;
  String _citySearchQuery = '';

  List<Map<String, dynamic>> get _filteredCities {
    final query = _citySearchQuery.trim().toLowerCase();
    if (query.isEmpty) return _cities;
    return _cities.where((city) =>
      city['city_name'].toString().toLowerCase().contains(query)
    ).toList();
  }

  Map<String, dynamic>? get _selectedCity {"""
if old not in s:
    raise SystemExit('Could not locate city state insertion point; source was not changed.')
s = s.replace(old, new, 1)
old = """                      else
                        DropdownButtonFormField<String>(
                          value: _selectedCityId,
                          decoration: const InputDecoration(labelText: 'اختر مدينة التوصيل', prefixIcon: Icon(Icons.location_city_outlined)),
                          items: _cities.map((city) => DropdownMenuItem<String>(
                            value: city['id'].toString(),
                            child: Text('${city['city_name']} — ${(city['delivery_fee'] as num).toStringAsFixed(2)} د.ل'),
                          )).toList(),
                          onChanged: (value) => setState(() => _selectedCityId = value),
                        ),"""
new = """                      else ...[
                        TextField(
                          key: const ValueKey('ASTRO_DELIVERY_CITY_SEARCH_PATCH'),
                          onChanged: (value) => setState(() => _citySearchQuery = value),
                          decoration: InputDecoration(
                            labelText: 'ابحث عن مدينتك',
                            hintText: 'اكتب اسم المدينة...',
                            prefixIcon: const Icon(Icons.search),
                            suffixIcon: _citySearchQuery.isEmpty
                                ? null
                                : IconButton(
                                    tooltip: 'مسح البحث',
                                    icon: const Icon(Icons.close),
                                    onPressed: () => setState(() => _citySearchQuery = ''),
                                  ),
                            filled: true,
                            fillColor: Colors.white,
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(14),
                            ),
                          ),
                        ),
                        const SizedBox(height: 8),
                        if (_filteredCities.isEmpty)
                          const Padding(
                            padding: EdgeInsets.all(14),
                            child: Center(
                              child: Text('لم يتم العثور على المدينة', style: TextStyle(color: Color(0xFF8492A3))),
                            ),
                          )
                        else
                          Container(
                            constraints: const BoxConstraints(maxHeight: 230),
                            decoration: BoxDecoration(
                              color: Colors.white,
                              border: Border.all(color: const Color(0xFFE2E8F0)),
                              borderRadius: BorderRadius.circular(14),
                            ),
                            child: ListView.separated(
                              shrinkWrap: true,
                              padding: EdgeInsets.zero,
                              itemCount: _filteredCities.length,
                              separatorBuilder: (_, __) => const Divider(height: 1, indent: 14, endIndent: 14),
                              itemBuilder: (context, index) {
                                final city = _filteredCities[index];
                                final cityId = city['id'].toString();
                                final selected = cityId == _selectedCityId;
                                return ListTile(
                                  dense: true,
                                  selected: selected,
                                  selectedTileColor: const Color(0xFFEAF4FF),
                                  title: Text(city['city_name'].toString(), style: const TextStyle(fontWeight: FontWeight.w700)),
                                  trailing: Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Text('${(city['delivery_fee'] as num).toStringAsFixed(2)} د.ل'),
                                      if (selected) const Padding(
                                        padding: EdgeInsetsDirectional.only(start: 6),
                                        child: Icon(Icons.check_circle, color: astroBlue, size: 18),
                                      ),
                                    ],
                                  ),
                                  onTap: () => setState(() => _selectedCityId = cityId),
                                );
                              },
                            ),
                          ),
                      ],"""
if old not in s:
    raise SystemExit('Could not locate original city dropdown; source was not changed.')
s = s.replace(old, new, 1)
p.write_text(s)
print('Delivery city search patch applied and verified.')
