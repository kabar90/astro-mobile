import 'dart:math';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../main.dart';
import '../services/notification_service.dart';

class BundleCheckoutScreen extends StatefulWidget {
  final int offerId;
  final String offerName;
  final double bundlePrice;
  const BundleCheckoutScreen({super.key, required this.offerId, required this.offerName, required this.bundlePrice});
  @override
  State<BundleCheckoutScreen> createState() => _BundleCheckoutScreenState();
}

class _BundleCheckoutScreenState extends State<BundleCheckoutScreen> {
  final db = Supabase.instance.client;
  final name = TextEditingController();
  final phone = TextEditingController();
  final address = TextEditingController();
  List<Map<String,dynamic>> cities = [];
  String? cityId;
  String delivery = 'delivery', payment = 'cash';
  Map<String,dynamic>? bank;
  XFile? receipt;
  bool loading = true, sending = false;

  Map<String,dynamic>? get city {
    for (final c in cities) { if (c['id'].toString() == cityId) return c; }
    return null;
  }
  double get fee => delivery == 'delivery' ? ((city?['delivery_fee'] as num?)?.toDouble() ?? 0) : 0;

  @override
  void initState() {
    super.initState();
    final user = db.auth.currentUser;
    final meta = user?.userMetadata ?? {};
    name.text = (meta['full_name'] ?? '').toString();
    phone.text = (meta['phone'] ?? user?.phone ?? '').toString();
    load();
  }
  @override
  void dispose() { name.dispose(); phone.dispose(); address.dispose(); super.dispose(); }

  void msg(String s) {
    if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(s)));
  }
  Future<void> load() async {
    try {
      final rows = await db.from('delivery_cities').select('id,city_name,delivery_fee').eq('is_active',true).order('city_name');
      final b = await db.from('bank_transfer_settings').select().eq('id',1).maybeSingle();
      if (!mounted) return;
      setState(() { cities = List<Map<String,dynamic>>.from(rows); bank = b; loading = false; });
    } catch (e) { if (mounted) setState(() => loading = false); msg('تعذر تحميل بيانات الدفع والتوصيل: ' + e.toString()); }
  }
  Future<void> pickReceipt() async {
    final f = await ImagePicker().pickImage(source: ImageSource.gallery,imageQuality:80);
    if (f != null && mounted) setState(() => receipt = f);
  }
  String receiptPath() {
    final r = Random.secure().nextInt(0x7fffffff).toRadixString(16);
    final m = receipt?.mimeType?.toLowerCase() ?? '';
    final n = receipt?.name.toLowerCase() ?? '';
    final ext = m == 'image/png' || n.endsWith('.png') ? 'png' : (m == 'image/webp' || n.endsWith('.webp') ? 'webp' : 'jpg');
    return 'orders/' + DateTime.now().millisecondsSinceEpoch.toString() + '_' + r + '.' + ext;
  }
  Future<void> submit() async {
    if (db.auth.currentUser == null) { msg('يرجى تسجيل الدخول قبل شراء الباقة'); return; }
    if (name.text.trim().isEmpty || phone.text.trim().isEmpty) { msg('يرجى إدخال الاسم ورقم الهاتف'); return; }
    if (delivery == 'delivery' && cityId == null) { msg('يرجى اختيار مدينة التوصيل'); return; }
    if (delivery == 'delivery' && address.text.trim().isEmpty) { msg('يرجى إدخال عنوان التوصيل'); return; }
    if (payment == 'transfer' && receipt == null) { msg('يرجى إرفاق إيصال التحويل'); return; }
    if (payment == 'transfer' && (bank == null || (bank!['account_number']?.toString().trim().isEmpty ?? true))) {
      msg('بيانات الحساب المصرفي غير مكتملة'); return;
    }
    setState(() => sending = true);
    try {
      String? path;
      if (payment == 'transfer') {
        path = receiptPath();
        await db.storage.from('receipts').uploadBinary(path, await receipt!.readAsBytes(),
          fileOptions: FileOptions(upsert:false,contentType:receipt!.mimeType ?? 'image/jpeg'));
      }
      final id = await db.rpc('astro_create_offer_order',params:{
        'p_customer_name':name.text.trim(),'p_customer_phone':phone.text.trim(),
        'p_customer_address':delivery == 'pickup' ? '' : address.text.trim(),
        'p_delivery_method':delivery,'p_payment_method':payment,
        'p_offer_id':widget.offerId,'p_quantity':1,'p_product_id':null,
        'p_receipt_path':path,'p_delivery_city':delivery == 'delivery' ? cityId : null,
      });
      await NotificationService.instance.bindCurrentCustomerPhone(phone.text.trim());
      if (!mounted) return;
      await showDialog<void>(context:context,barrierDismissible:false,builder:(d)=>AlertDialog(
        title:const Text('تم استلام طلب الباقة بنجاح'),
        content:Text('رقم الطلب: ' + id.toString() + '\n' + (payment == 'transfer' ? 'سيتم مراجعة إيصال التحويل والتواصل معك.' : 'سنتواصل معك لتأكيد الطلب.')),
        actions:[TextButton(onPressed:(){Navigator.of(d).pop();Navigator.of(context).popUntil((r)=>r.isFirst);},child:const Text('حسناً'))],
      ));
    } catch(e) { msg('تعذر إرسال طلب الباقة: ' + e.toString()); }
    finally { if (mounted) setState(()=>sending=false); }
  }

  Widget bankRow(String label,String key) {
    final v = bank?[key]?.toString().trim() ?? '';
    if (v.isEmpty) return const SizedBox.shrink();
    return Padding(padding:const EdgeInsets.symmetric(vertical:4),child:Row(children:[
      SizedBox(width:105,child:Text(label,style:const TextStyle(color:Colors.blueGrey,fontSize:12))),
      Expanded(child:SelectableText(v,style:const TextStyle(fontWeight:FontWeight.w700))),
    ]));
  }
  Widget summary(String label,double value,{bool bold=false}) => Padding(
    padding:const EdgeInsets.symmetric(vertical:3),child:Row(mainAxisAlignment:MainAxisAlignment.spaceBetween,children:[
      Text(label,style:TextStyle(fontWeight:bold?FontWeight.w900:FontWeight.normal)),
      Text(value.toStringAsFixed(2)+' د.ل',style:TextStyle(fontWeight:bold?FontWeight.w900:FontWeight.normal)),
    ]));

  @override
  Widget build(BuildContext context) {
    return Scaffold(backgroundColor:astroBackground,appBar:AppBar(title:const Text('شراء الباقة')),
      body:loading?const Center(child:CircularProgressIndicator()):ListView(padding:const EdgeInsets.all(18),children:[
        Card(child:Padding(padding:const EdgeInsets.all(14),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
          Text(widget.offerName,style:const TextStyle(fontSize:18,fontWeight:FontWeight.w900,color:astroNavy)),
          Text('سعر الباقة: '+widget.bundlePrice.toStringAsFixed(2)+' د.ل',style:const TextStyle(fontSize:18,fontWeight:FontWeight.w900,color:Color(0xFFE44755))),
        ]))),
        const SizedBox(height:14),
        const Text('بيانات العميل',style:TextStyle(fontWeight:FontWeight.w900,color:astroNavy)),
        TextField(controller:name,decoration:const InputDecoration(labelText:'الاسم الكامل',border:OutlineInputBorder())),
        const SizedBox(height:8),
        TextField(controller:phone,keyboardType:TextInputType.phone,decoration:const InputDecoration(labelText:'رقم الهاتف',border:OutlineInputBorder())),
        const SizedBox(height:14),
        const Text('طريقة الاستلام',style:TextStyle(fontWeight:FontWeight.w900,color:astroNavy)),
        RadioListTile<String>(value:'delivery',groupValue:delivery,title:const Text('توصيل إلى العنوان'),onChanged:sending?null:(v)=>setState(()=>delivery=v!)),
        RadioListTile<String>(value:'pickup',groupValue:delivery,title:const Text('استلام من المتجر'),onChanged:sending?null:(v)=>setState(()=>delivery=v!)),
        if(delivery=='delivery') ...[
          DropdownButtonFormField<String>(value:cityId,decoration:const InputDecoration(labelText:'مدينة التوصيل',border:OutlineInputBorder()),
            items:cities.map((c)=>DropdownMenuItem<String>(value:c['id'].toString(),child:Text(c['city_name'].toString()+' — '+(((c['delivery_fee'] as num?)?.toDouble()??0).toStringAsFixed(2))+' د.ل'))).toList(),
            onChanged:sending?null:(v)=>setState(()=>cityId=v)),
          const SizedBox(height:8),
          TextField(controller:address,maxLines:2,decoration:const InputDecoration(labelText:'العنوان بالتفصيل',border:OutlineInputBorder())),
        ],
        const SizedBox(height:14),
        const Text('طريقة الدفع',style:TextStyle(fontWeight:FontWeight.w900,color:astroNavy)),
        RadioListTile<String>(value:'cash',groupValue:payment,title:const Text('نقداً عند الاستلام'),onChanged:sending?null:(v)=>setState(()=>payment=v!)),
        RadioListTile<String>(value:'transfer',groupValue:payment,title:const Text('تحويل مصرفي'),onChanged:sending?null:(v)=>setState(()=>payment=v!)),
        if(payment=='transfer') ...[
          Card(child:Padding(padding:const EdgeInsets.all(12),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
            const Text('بيانات الحساب المصرفي',style:TextStyle(fontWeight:FontWeight.w900)),
            bankRow('المصرف','bank_name'),bankRow('صاحب الحساب','account_holder'),bankRow('الفرع','branch_name'),
            bankRow('رقم الحساب','account_number'),bankRow('IBAN','iban'),bankRow('التعليمات','account_details'),
          ]))),
          OutlinedButton.icon(onPressed:sending?null:pickReceipt,icon:const Icon(Icons.upload_file),label:Text(receipt==null?'اختيار صورة إيصال التحويل':receipt!.name)),
          if(receipt!=null) const Text('تم اختيار الإيصال',style:TextStyle(color:Colors.green)),
        ],
        Card(child:Padding(padding:const EdgeInsets.all(14),child:Column(children:[
          summary('سعر الباقة',widget.bundlePrice),summary('رسوم التوصيل',fee),const Divider(),
          summary('الإجمالي',widget.bundlePrice+fee,bold:true),
        ]))),
        const SizedBox(height:14),
        SizedBox(width:double.infinity,child:ElevatedButton(onPressed:sending?null:submit,
          style:ElevatedButton.styleFrom(backgroundColor:astroBlue,foregroundColor:Colors.white,padding:const EdgeInsets.all(16)),
          child:Text(sending?'جارٍ إرسال الطلب...':'تأكيد شراء الباقة'))),
      ]));
  }
}


class BundleDetailsScreen extends StatelessWidget {
  final int offerId;
  final String offerName;
  final double bundlePrice;
  final List<Map<String, dynamic>> products;

  const BundleDetailsScreen({
    super.key,
    required this.offerId,
    required this.offerName,
    required this.bundlePrice,
    required this.products,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: astroBackground,
      appBar: AppBar(title: const Text('تفاصيل الباقة')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(offerName, textAlign: TextAlign.right,
                    style: const TextStyle(fontSize: 21, fontWeight: FontWeight.w900, color: astroNavy)),
                  const SizedBox(height: 8),
                  const Text('تتضمن هذه الباقة المنتجات التالية معاً:',
                    textAlign: TextAlign.right, style: TextStyle(fontWeight: FontWeight.w700)),
                  const SizedBox(height: 12),
                  for (final product in products)
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 7),
                      child: Row(
                        children: [
                          ClipRRect(
                            borderRadius: BorderRadius.circular(9),
                            child: SizedBox(width: 76, height: 76,
                              child: Image.network((product['imageUrl'] ?? '').toString(), fit: BoxFit.cover,
                                errorBuilder: (_, __, ___) => const Icon(Icons.image_not_supported))),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                Text((product['name'] ?? '').toString(), textAlign: TextAlign.right,
                                  style: const TextStyle(fontWeight: FontWeight.w900, color: astroNavy)),
                                if ((product['description'] ?? '').toString().trim().isNotEmpty)
                                  Text((product['description'] ?? '').toString(), maxLines: 3, overflow: TextOverflow.ellipsis,
                                    textAlign: TextAlign.right,
                                    style: const TextStyle(fontSize: 12, color: Colors.blueGrey)),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  const Divider(height: 24),
                  const Text('سعر المجموعة كاملة', textAlign: TextAlign.right,
                    style: TextStyle(fontWeight: FontWeight.w800)),
                  Text(bundlePrice.toStringAsFixed(2) + ' د.ل',
                    textAlign: TextAlign.right,
                    style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w900, color: Color(0xFFE44755))),
                  const SizedBox(height: 6),
                  const Text('السعر يشمل المنتجات المذكورة معاً، ولا يمكن شراء كل منتج منفرداً من هذا العرض.',
                    textAlign: TextAlign.right, style: TextStyle(color: Colors.blueGrey)),
                ],
              ),
            ),
          ),
          const SizedBox(height: 14),
          SizedBox(
            height: 52,
            child: ElevatedButton.icon(
              style: ElevatedButton.styleFrom(backgroundColor: astroBlue, foregroundColor: Colors.white),
              onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) =>
                BundleCheckoutScreen(offerId: offerId, offerName: offerName, bundlePrice: bundlePrice))),
              icon: const Icon(Icons.card_giftcard_rounded),
              label: const Text('شراء الباقة كاملة', style: TextStyle(fontWeight: FontWeight.w900)),
            ),
          ),
        ],
      ),
    );
  }
}
