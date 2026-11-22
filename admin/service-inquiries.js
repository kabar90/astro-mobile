(() => {
 const $=id=>document.getElementById(id), labels={maintenance:'الصيانة - حضور شخصي',software:'السوفتوير - حضور شخصي',remote_programming:'البرمجة عن بُعد'};
 const states=[['new','جديد'],['in_progress','قيد المراجعة'],['answered','تم الرد / متوفر'],['unavailable','غير متوفر'],['payment_submitted','إيصال الدفع مرسل'],['paid','تم تأكيد الدفع'],['closed','مغلق']];
 let active=null;
 function init(){
  const nav=document.querySelector('#dash nav'),dash=$('dash');if(!nav||!dash||$('serviceInquiriesView'))return;
  const b=document.createElement('button');b.textContent='استفسارات الخدمات';b.dataset.view='serviceInquiriesView';nav.append(b);
  const p=document.createElement('section');p.id='serviceInquiriesView';p.className='card hide';
  p.innerHTML='<h2>استفسارات الخدمات</h2><p>الصيانة والسوفتوير بالحضور الشخصي والدفع داخل المحل. البرمجة عن بُعد بتحويل مصرفي.</p><button id="svcRefresh">تحديث</button><p id="svcStatus"></p><div id="svcList"></div><div id="svcEditor" class="hide"><hr><h3 id="svcTitle"></h3><p id="svcInfo"></p><p id="svcContact"></p><p id="svcReceipt"></p><label>رد الإدارة<textarea id="svcReply"></textarea></label><label>السعر بالدينار الليبي<input id="svcPrice" type="number" min="0" step="0.01"></label><label>الحالة<select id="svcState"></select></label><button id="svcSave">حفظ الرد</button><span id="svcMsg"></span></div>';dash.append(p);
  const st=document.createElement('style');st.textContent='#serviceInquiriesView article{border:1px solid #ddd;border-radius:12px;padding:12px;margin:10px 0}#serviceInquiriesView label{display:block;margin:10px 0}#serviceInquiriesView input,#serviceInquiriesView textarea,#serviceInquiriesView select{display:block;width:100%;padding:10px}';document.head.append(st);
  $('svcState').innerHTML=states.map(x=>'<option value="'+x[0]+'">'+x[1]+'</option>').join('');
  b.onclick=()=>{dash.querySelectorAll(':scope > .card').forEach(x=>x.classList.add('hide'));p.classList.remove('hide');nav.querySelectorAll('button').forEach(x=>x.classList.remove('active'));b.classList.add('active');load();};
  $('svcRefresh').onclick=load;$('svcSave').onclick=save;
 }
 const sb=()=>window.sb||window.supabaseClient;
 async function load(){
  $('svcStatus').textContent='جارٍ التحميل...';$('svcList').replaceChildren();$('svcEditor').classList.add('hide');
  const {data,error}=await sb().from('service_inquiries').select('*').order('created_at',{ascending:false}).limit(200);
  if(error){$('svcStatus').textContent='تعذر التحميل: '+error.message;return;}
  $('svcStatus').textContent='عدد الاستفسارات: '+(data||[]).length;
  (data||[]).forEach(r=>{const a=document.createElement('article'),h=document.createElement('h3'),d=document.createElement('p'),b=document.createElement('button');h.textContent='#'+r.id+' · '+(labels[r.service_type]||r.service_type)+' · '+r.device_model;d.textContent=r.request_details+' | '+r.status;b.textContent='فتح والرد';b.onclick=()=>edit(r);a.append(h,d,b);$('svcList').append(a);});
 }
 async function edit(r){
  active=r;$('svcEditor').classList.remove('hide');$('svcTitle').textContent='#'+r.id+' · '+(labels[r.service_type]||r.service_type)+' · '+r.device_model;$('svcInfo').textContent=r.request_details;$('svcReply').value=r.admin_reply||'';$('svcPrice').value=r.quoted_price??'';$('svcState').value=r.status;
  $('svcContact').textContent=r.service_type==='remote_programming'?'واتساب: '+(r.whatsapp_phone||'لم يحدد')+' | الموافقة: '+(r.whatsapp_consent?'نعم':'لا'):'الدفع داخل المحل.';
  $('svcReceipt').replaceChildren();if(r.receipt_path){const {data}=await sb().storage.from('receipts').createSignedUrl(r.receipt_path,3600);if(data?.signedUrl){const a=document.createElement('a');a.href=data.signedUrl;a.target='_blank';a.rel='noopener';a.textContent='فتح إيصال التحويل';$('svcReceipt').append(a);}}
  $('svcEditor').scrollIntoView({behavior:'smooth'});
 }
 async function save(){
  if(!active)return;const price=$('svcPrice').value===''?null:Number($('svcPrice').value),state=$('svcState').value;if(price!==null&&(!Number.isFinite(price)||price<0)){ $('svcMsg').textContent='السعر غير صحيح';return;}if(state==='answered'&&price===null){$('svcMsg').textContent='أدخل السعر أولاً';return;}
  const patch={admin_reply:$('svcReply').value.trim()||null,quoted_price:price,status:state,updated_at:new Date().toISOString()};if(state==='paid')patch.payment_confirmed_at=new Date().toISOString();
  const {error}=await sb().from('service_inquiries').update(patch).eq('id',active.id);$('svcMsg').textContent=error?'فشل الحفظ: '+error.message:'تم الحفظ';if(!error)load();
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
