import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../main.dart';

class ServiceInquiriesScreen extends StatefulWidget {
  const ServiceInquiriesScreen({super.key});
  @override
  State<ServiceInquiriesScreen> createState() => _ServiceInquiriesScreenState();
}
class _ServiceInquiriesScreenState extends State<ServiceInquiriesScreen> {
  final db = Supabase.instance.client;
  final model = TextEditingController(), details = TextEditingController();
  String type = 'maintenance';
  bool busy = false, loading = true;
  List<Map<String,dynamic>> rows = [];
  static const types = {'maintenance':'الصيانة','software':'السوفتوير','remote_programming':'برمجة هاتفك النقال'};
  @override void initState(){super.initState();load();}
  @override void dispose(){model.dispose();details.dispose();super.dispose();}
  void msg(String s){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(s)));}
  Future<void> load() async {
    try { final r=await db.from('service_inquiries').select().eq('user_id',db.auth.currentUser!.id).order('created_at',ascending:false); if(mounted)setState(()=>rows=List<Map<String,dynamic>>.from(r)); }
    catch(e){debugPrint('service inquiries: $e');} finally {if(mounted)setState(()=>loading=false);}
  }
  Future<void> send() async {
    if(db.auth.currentUser==null){msg('يرجى تسجيل الدخول أولاً.');return;}
    if(model.text.trim().length<2||details.text.trim().length<3){msg('أدخل موديل الجهاز والتفاصيل المطلوبة.');return;}
    setState(()=>busy=true);
    try {await db.from('service_inquiries').insert({'user_id':db.auth.currentUser!.id,'service_type':type,'device_model':model.text.trim(),'request_details':details.text.trim()});model.clear();details.clear();msg('تم إرسال استفسارك.');await load();}
    catch(e){msg('تعذر إرسال الاستفسار: $e');} finally {if(mounted)setState(()=>busy=false);}
  }
  Future<void> pay(Map<String,dynamic> row) async {
    final phone=TextEditingController(); bool consent=false;
    final ok=await showDialog<bool>(context:context,builder:(c)=>StatefulBuilder(builder:(c,setLocal)=>AlertDialog(
      title:const Text('التواصل عبر واتساب'),
      content:Column(mainAxisSize:MainAxisSize.min,children:[
        const Text('يرجى إدخال رقم هاتف مفعل عليه تطبيق WhatsApp، حيث سيتم التواصل معك عبر واتساب بعد تأكيد عملية الدفع لمتابعة تنفيذ خدمة البرمجة عن بُعد.'),
        TextField(controller:phone,keyboardType:TextInputType.phone,decoration:const InputDecoration(labelText:'رقم واتساب')),
        CheckboxListTile(value:consent,onChanged:(v)=>setLocal(()=>consent=v??false),title:const Text('أوافق على التواصل معي عبر واتساب بعد الدفع.'),controlAffinity:ListTileControlAffinity.leading)
      ]),
      actions:[TextButton(onPressed:()=>Navigator.pop(c,false),child:const Text('إلغاء')),ElevatedButton(onPressed:()=>Navigator.pop(c,consent&&phone.text.trim().length>=7),child:const Text('متابعة'))]
    )));
    if(ok!=true){phone.dispose();return;}
    await payment(row,phone.text.trim()); phone.dispose();
  }
  Future<void> payment(Map<String,dynamic> row,String phone) async {
    Map<String,dynamic>? bank; XFile? receipt; bool sending=false;
    try{bank=await db.from('bank_transfer_settings').select().eq('id',1).maybeSingle();}catch(_){}
    if(!mounted)return;
    await showDialog<void>(context:context,builder:(c)=>StatefulBuilder(builder:(c,setLocal)=>AlertDialog(
      title:const Text('تحويل قيمة البرمجة عن بُعد'),
      content:SingleChildScrollView(child:Column(crossAxisAlignment:CrossAxisAlignment.start,mainAxisSize:MainAxisSize.min,children:[
        Text('المبلغ: ${row['quoted_price']} د.ل',style:const TextStyle(fontWeight:FontWeight.bold)),
        if(bank==null) const Text('تعذر تحميل بيانات المصرف.') else ...[
          Text('المصرف: ${bank!['bank_name']??'-'}'),Text('صاحب الحساب: ${bank!['account_holder']??'-'}'),Text('رقم الحساب: ${bank!['account_number']??'-'}'),
          if((bank!['iban']??'').toString().isNotEmpty)Text('IBAN: ${bank!['iban']}')
        ],
        OutlinedButton(onPressed:sending?null:()async{final f=await ImagePicker().pickImage(source:ImageSource.gallery,imageQuality:80);if(f!=null)setLocal(()=>receipt=f);},child:Text(receipt==null?'إرفاق إيصال التحويل':receipt!.name)),
        const Text('سيتم التواصل معك بعد تأكيد الدفع فقط.')
      ])),
      actions:[TextButton(onPressed:sending?null:()=>Navigator.pop(c),child:const Text('إلغاء')),ElevatedButton(onPressed:sending||receipt==null||bank==null?null:()async{
        setLocal(()=>sending=true);
        try{
          final path='service-payments/${row['id']}_${DateTime.now().millisecondsSinceEpoch}.jpg';
          await db.storage.from('receipts').uploadBinary(path,await receipt!.readAsBytes(),fileOptions:FileOptions(upsert:false,contentType:receipt!.mimeType??'image/jpeg'));
          await db.rpc('astro_submit_remote_service_payment',params:{'p_inquiry_id':row['id'],'p_whatsapp_phone':phone,'p_receipt_path':path});
          if(c.mounted)Navigator.pop(c);msg('تم إرسال الإيصال. بانتظار تأكيد الدفع.');await load();
        }catch(e){setLocal(()=>sending=false);msg('تعذر إرسال الإيصال: $e');}
      },child:Text(sending?'جارٍ الإرسال':'إرسال الإيصال'))]
    )));
  }
  String status(String s)=>{'new':'جديد','in_progress':'قيد المراجعة','answered':'تم الرد','unavailable':'غير متوفر','payment_submitted':'الإيصال قيد المراجعة','paid':'تم تأكيد الدفع','closed':'مغلق'}[s]??s;
  @override Widget build(BuildContext context)=>Scaffold(
    appBar:AppBar(title:const Text('خدمات الصيانة والبرمجة'),actions:[IconButton(onPressed:load,icon:const Icon(Icons.refresh))]),
    body:db.auth.currentUser==null?const Center(child:Text('يرجى تسجيل الدخول أولاً.')):RefreshIndicator(onRefresh:load,child:ListView(padding:const EdgeInsets.all(16),children:[
      Card(child:Padding(padding:const EdgeInsets.all(16),child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
        const Text('إرسال استفسار جديد',style:TextStyle(fontSize:18,fontWeight:FontWeight.bold,color:astroNavy)),
        DropdownButtonFormField<String>(value:type,decoration:const InputDecoration(labelText:'نوع الخدمة'),items:types.entries.map((e)=>DropdownMenuItem(value:e.key,child:Text(e.value))).toList(),onChanged:(v)=>setState(()=>type=v??type)),
        const SizedBox(height:10),TextField(controller:model,decoration:const InputDecoration(labelText:'نوع الجهاز / الموديل')),
        const SizedBox(height:10),TextField(controller:details,minLines:2,maxLines:4,decoration:InputDecoration(labelText:type=='maintenance'?'اشرح العطل':type=='software'?'نوع السوفتوير المطلوب':'نوع البرمجة المطلوبة')),
        Padding(padding:const EdgeInsets.symmetric(vertical:8),child:Text(type=='remote_programming'?'يمكن برمجة بعض أعطال الهاتف عن بُعد في حالات معينة، بعد مراجعة نوع العطل وتأكيد إمكانية معالجته. في حال توفر الخدمة عن بُعد، ستظهر لك التكلفة وطريقة الدفع بعد رد الإدارة.':'تتطلب خدمتا الصيانة والسوفتوير الحضور الشخصي إلى المحل، والدفع داخل المحل.',style:const TextStyle(color:Colors.black54))),
        ElevatedButton(onPressed:busy?null:send,child:Text(busy?'جارٍ الإرسال':'إرسال الاستفسار'))
      ]))),
      const SizedBox(height:14),const Text('استفساراتي والردود',style:TextStyle(fontSize:18,fontWeight:FontWeight.bold,color:astroNavy)),
      if(loading)const Center(child:CircularProgressIndicator()) else if(rows.isEmpty)const Text('لا توجد استفسارات.') else ...rows.map((r)=>Card(margin:const EdgeInsets.only(top:10),child:Padding(padding:const EdgeInsets.all(14),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
        Text(types[r['service_type']]??'خدمة',style:const TextStyle(fontWeight:FontWeight.bold,color:astroNavy)),
        Text('الجهاز: ${r['device_model']}'),Text('التفاصيل: ${r['request_details']}'),Text('الحالة: ${status(r['status']??'new')}'),
        if((r['admin_reply']??'').toString().isNotEmpty)Text('رد الإدارة: ${r['admin_reply']}'),
        if(r['quoted_price']!=null)Text('السعر: ${r['quoted_price']} د.ل'),
        if(r['service_type']=='remote_programming'&&r['status']=='answered'&&r['quoted_price']!=null)ElevatedButton(onPressed:()=>pay(r),child:const Text('دفع قيمة البرمجة وإرسال الإيصال')),
        if(r['status']=='payment_submitted')const Text('الإيصال قيد المراجعة.'),
        if(r['status']=='paid')const Text('تم تأكيد الدفع. سيتم التواصل معك عبر واتساب.')
      ]))))
    ]))
  );
}
