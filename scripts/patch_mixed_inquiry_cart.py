from pathlib import Path
root=Path("astro_mobile")
def edit(path, old, new):
 p=root/path; s=p.read_text(encoding="utf-8")
 if old not in s: raise SystemExit(f"Missing patch anchor in {path}: {old[:80]}")
 p.write_text(s.replace(old,new,1),encoding="utf-8")

p=root/"lib/services/cart_service.dart"; s=p.read_text(encoding="utf-8")
if "bool get isInquiryOption" not in s:
 a=s.index("class CartLine {"); b=s.index("\nclass CartService",a)
 s=s[:a]+'''class CartLine {
  final Product? product;
  final String? color;
  final String? inquiryId;
  final String? optionId;
  final String? imageUrl;
  final String? inquiryDeviceModel;
  final double? inquiryPrice;
  int quantity;
  CartLine({required this.product, required this.color, this.inquiryId, this.optionId,
    this.imageUrl, this.inquiryDeviceModel, this.inquiryPrice, this.quantity=1});
  bool get isInquiryOption => inquiryId != null && optionId != null;
  String get name => isInquiryOption ? '${inquiryDeviceModel ?? 'خيار استفسار'} - خيار متوفر' : (product?.name ?? 'منتج');
  double get price => isInquiryOption ? (inquiryPrice ?? 0) : (product?.price ?? 0);
  String get displayImage => isInquiryOption ? (imageUrl ?? '') : (product?.imageUrl ?? '');
  double get total => price * quantity;
  Map<String,dynamic> toOrderJson() => isInquiryOption ? {
    'item_type':'inquiry_option','product_id':null,'product_name':name,'quantity':quantity,
    'unit_price':price,'color':null,'inquiry_id':inquiryId,'option_id':optionId,'image_url':imageUrl
  } : {
    'item_type':'product','product_id':product!.id,'product_name':product!.name,
    'quantity':quantity,'unit_price':product!.price,'color':color
  };
}
''' + s[b:]
 s=s.replace('(item) => item.product.id == product.id && item.color == color,',
   '(item) => !item.isInquiryOption && item.product?.id == product.id && item.color == color,')
 anchor='  void changeQuantity(CartLine line, int delta) {'
 method='''  bool addInquiryOption({required String inquiryId, required String optionId,
    required String imageUrl, required double price, required String deviceModel}) {
    if(inquiryId.isEmpty || optionId.isEmpty || imageUrl.isEmpty || price < 0) return false;
    if(_items.any((x)=>x.inquiryId==inquiryId && x.optionId==optionId)) return false;
    _items.add(CartLine(product:null,color:null,inquiryId:inquiryId,optionId:optionId,
      imageUrl:imageUrl,inquiryDeviceModel:deviceModel,inquiryPrice:price));
    notifyListeners(); return true;
  }

'''
 s=s.replace(anchor,method+anchor,1)
 s=s.replace('  void changeQuantity(CartLine line, int delta) {\n    line.quantity += delta;',
   '  void changeQuantity(CartLine line, int delta) {\n    if(line.isInquiryOption && delta > 0) return;\n    line.quantity += delta;')
 p.write_text(s,encoding="utf-8")

p=root/"lib/screens/product_inquiry_inline.dart"; s=p.read_text(encoding="utf-8")
if "CartService.instance.addInquiryOption" not in s:
 s=s.replace("import '../models/product.dart';","import '../models/product.dart';\nimport '../services/cart_service.dart';")
 old="""              final price = double.tryParse((image['price'] ?? '').toString());
              return SizedBox(
"""
 new="""              final price = double.tryParse((image['price'] ?? '').toString());
              final optionId = (image['option_id'] ?? '').toString();
              final inquiryId = (item['id'] ?? '').toString();
              final selected = image['selected'] == true;
              final expiresAt = DateTime.tryParse((image['expires_at'] ?? '').toString());
              final expired = expiresAt != null && !expiresAt.isAfter(DateTime.now());
              final canAdd = status == 'answered' && optionId.isNotEmpty && inquiryId.isNotEmpty &&
                  price != null && price >= 0 && !selected && !expired && url.isNotEmpty;
              return SizedBox(
"""
 if old not in s: raise SystemExit("Missing image option build anchor")
 s=s.replace(old,new,1)
 old="""                      Text(
                        price == null
                            ? 'السعر غير محدد'
                            : price.toStringAsFixed(2) + ' د.ل',
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          color: astroBlue,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
"""
 new="""                      Text(price == null ? 'السعر غير محدد' : price.toStringAsFixed(2) + ' د.ل',
                        textAlign: TextAlign.center,
                        style: const TextStyle(color: astroBlue,fontWeight: FontWeight.w900)),
                      const SizedBox(height: 6),
                      if (selected)
                        const Text('تم اختيار هذا الخيار',textAlign: TextAlign.center,
                          style: TextStyle(fontSize: 10,color: Colors.green,fontWeight: FontWeight.w700))
                      else if (expired)
                        const Text('انتهت صلاحية العرض',textAlign: TextAlign.center,
                          style: TextStyle(fontSize: 10,color: Colors.red,fontWeight: FontWeight.w700))
                      else
                        SizedBox(height: 34,child: ElevatedButton.icon(
                          onPressed: canAdd ? () {
                            final added=CartService.instance.addInquiryOption(
                              inquiryId:inquiryId,optionId:optionId,imageUrl:url,price:price!,
                              deviceModel:(item['device_model'] ?? '').toString());
                            _message(added ? 'تمت إضافة الخيار إلى السلة' : 'هذا الخيار موجود بالفعل في السلة');
                          } : null,
                          icon: const Icon(Icons.add_shopping_cart,size:14),
                          label: const Text('أضف للسلة',style: TextStyle(fontSize:10)),
                        )),
"""
 if old not in s: raise SystemExit("Missing image price widget anchor")
 s=s.replace(old,new,1); p.write_text(s,encoding="utf-8")

for screen in ["lib/screens/checkout_screen.dart","lib/screens/bank_transfer_screen.dart"]:
 p=root/screen; s=p.read_text(encoding="utf-8")
 old="""      final items = cart.items.map((item) => {
        'product_id': item.product.id,
        'product_name': item.product.name,
        'quantity': item.quantity,
        'unit_price': item.product.price,
        'color': item.color,
      }).toList();

      final result = await _db.rpc('astro_create_order', params: {
"""
 new="""      final items = cart.items.map((item) => item.toOrderJson()).toList();

      final result = await _db.rpc('astro_create_mixed_order', params: {
"""
 if old in s: s=s.replace(old,new,1)
 elif "astro_create_mixed_order" not in s: raise SystemExit(f"Missing checkout serialization in {screen}")
 if screen.endswith("checkout_screen.dart"):
  s=s.replace("items.every((item) => item.product.allowPointsPayment)",
    "items.every((item) => !item.isInquiryOption && (item.product?.allowPointsPayment ?? false))")
  s=s.replace("'product_id': item.product.id,","'product_id': item.product!.id,")
 p.write_text(s,encoding="utf-8")

p=root/"lib/screens/cart_screen.dart"; s=p.read_text(encoding="utf-8")
s=s.replace("item.product.imageUrl.isNotEmpty","item.displayImage.isNotEmpty")
s=s.replace("imageUrl: item.product.imageUrl,","imageUrl: item.displayImage,")
s=s.replace("item.product.name,","item.name,")
s=s.replace("'\u0024{item.product.price.toStringAsFixed(2)} د.ل'","'\u0024{item.price.toStringAsFixed(2)} د.ل'")
s=s.replace("'\u0024{(item.product.price * item.quantity).toStringAsFixed(2)} د.ل'","'\u0024{item.total.toStringAsFixed(2)} د.ل'")
p.write_text(s,encoding="utf-8")
print("Mixed inquiry cart patch applied")
