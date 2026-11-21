import { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm";
import { SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, ADMIN_EMAIL } from "./supabase-config.js";

const sb = createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY);
const $ = id => document.getElementById(id);
const sectionNames = {17:"الكفرات",34:"لاصقة عدسة الكاميرا",40:"لاصقة الشاشة"};
let activeInquiry = null;
let products = [];

function message(text, error=false) {
  const el=$("inquiryAdminMsg");
  if(el){el.textContent=text;el.style.color=error?"#b42318":"#16734a";}
}
function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}
async function loadInquiries() {
  const list=$("inquiryAdminList");
  if(!list)return;
  list.textContent="جارٍ تحميل الاستفسارات...";
  const {data,error}=await sb.from("product_inquiries")
    .select("id,user_id,category_id,device_model,customer_note,status,admin_reply,recommended_product_ids,created_at")
    .order("created_at",{ascending:false}).limit(100);
  if(error){list.textContent="تعذر تحميل الاستفسارات: "+error.message;return;}
  if(!data?.length){list.textContent="لا توجد استفسارات حتى الآن.";return;}
  list.replaceChildren();
  data.forEach(item=>{
    const card=document.createElement("article");
    card.className="item";
    card.style.cssText="display:block;background:#fff;color:#172033;border:1px solid #ddd;border-radius:12px;padding:14px;margin:12px 0";
    const title=document.createElement("h3");
    title.textContent="#"+item.id+" · "+(sectionNames[item.category_id]||"قسم غير معروف")+" · "+item.device_model;
    const info=document.createElement("p");
    info.textContent="الحالة: "+item.status+" | المستخدم: "+item.user_id+" | "+new Date(item.created_at).toLocaleString("ar-LY");
    const note=document.createElement("p");
    note.textContent=item.customer_note||"لا توجد ملاحظات إضافية.";
    const open=document.createElement("button");
    open.type="button";open.textContent="فتح والرد";
    open.addEventListener("click",()=>openInquiry(item));
    card.append(title,info,note,open);
    list.append(card);
  });
}
async function loadProductsForCategory(categoryId) {
  // The inquiry category IDs are the store subcategory IDs (subcategory_id).
  // Filter by the numeric ID so similarly named categories cannot mix products.
  const {data,error}=await sb.from("products")
    .select("id,name,price,image_url,colors,category,subcategory_id,is_active")
    .eq("is_active",true)
    .eq("subcategory_id",categoryId)
    .order("name");
  if(error)throw error;
  return data||[];
}
async function openInquiry(item) {
  activeInquiry=item;
  $("inquiryReplyPanel").classList.remove("hide");
  $("inquiryReplyTitle").textContent="الرد على الاستفسار #"+item.id+" — "+sectionNames[item.category_id]+" — "+item.device_model;
  $("inquiryReplyText").value=item.admin_reply||"";
  $("inquiryStatus").value=item.status;
  $("inquiryProducts").textContent="جارٍ تحميل المنتجات المتاحة...";
  try{
    products=await loadProductsForCategory(item.category_id);
    const selected=new Set((item.recommended_product_ids||[]).map(String));
    const host=$("inquiryProducts");host.replaceChildren();
    if(!products.length){host.textContent="لا توجد منتجات نشطة مرتبطة باسم هذا القسم حالياً. يمكنك كتابة الرد دون إرفاق منتجات.";return;}
    products.forEach(p=>{
      const label=document.createElement("label");
      label.style.cssText="display:flex;align-items:center;gap:8px;padding:8px;border-bottom:1px solid #eee";
      const input=document.createElement("input");input.type="checkbox";input.value=String(p.id);input.checked=selected.has(String(p.id));
      const img=document.createElement("img");img.src=p.image_url||"";img.alt="";img.width=48;img.height=48;img.style.objectFit="cover";
      const text=document.createElement("span");text.textContent=p.name+" — "+Number(p.price||0).toFixed(2)+" د.ل"+(p.colors?" — "+p.colors:"");
      label.append(input,img,text);host.append(label);
    });
  }catch(e){$("inquiryProducts").textContent="تعذر تحميل المنتجات: "+e.message;}
  message("");
}
$("saveInquiryReply")?.addEventListener("click",async()=>{
  if(!activeInquiry)return;
  const button=$("saveInquiryReply");button.disabled=true;
  try{
    const ids=[...$("inquiryProducts").querySelectorAll('input[type="checkbox"]:checked')].map(x=>x.value);
    const status=$("inquiryStatus").value;
    const payload={admin_reply:$("inquiryReplyText").value.trim(),status,recommended_product_ids:ids};
    const {error}=await sb.from("product_inquiries").update(payload).eq("id",activeInquiry.id);
    if(error)throw error;
    message("تم حفظ الرد وتحديث حالة الاستفسار.");
    await loadInquiries();
  }catch(e){message("تعذر حفظ الرد: "+e.message,true);}
  finally{button.disabled=false;}
});
$("refreshInquiries")?.addEventListener("click",loadInquiries);
$("closeInquiryReply")?.addEventListener("click",()=>{$("inquiryReplyPanel").classList.add("hide");activeInquiry=null;});
document.querySelector('nav button[data-view="productInquiries"]')?.addEventListener("click",loadInquiries);
sb.auth.getSession().then(({data,error})=>{
  if(error){message(error.message,true);return;}
  const email=data.session?.user?.email?.toLowerCase();
  if(email===ADMIN_EMAIL.toLowerCase())loadInquiries();
});
sb.auth.onAuthStateChange((_event,session)=>{
  if(session?.user?.email?.toLowerCase()===ADMIN_EMAIL.toLowerCase())loadInquiries();
});
