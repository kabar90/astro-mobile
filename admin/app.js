import { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm";
import { SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, ADMIN_EMAIL } from "./supabase-config.js";

const supabase = createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY);
const $ = (id) => document.getElementById(id);
let currentUser = null;
let currentImageUrl = "";
const setMessage = (id, message, error = false) => {
  const el = $(id); el.textContent = message; el.style.color = error ? "#b42318" : "#16734a";
};

async function showSession(session) {
  const user = session?.user;
  if (user && (user.email || "").toLowerCase() === ADMIN_EMAIL.toLowerCase()) {
    currentUser = user;
    $("login").classList.add("hide"); $("dash").classList.remove("hide"); $("logout").classList.remove("hide");
    await Promise.all([loadProducts(), loadOrders()]);
  } else {
    currentUser = null;
    if (user) await supabase.auth.signOut();
    $("login").classList.remove("hide"); $("dash").classList.add("hide"); $("logout").classList.add("hide");
  }
}

$("loginBtn").addEventListener("click", async () => {
  const email = $("email").value.trim(); const password = $("password").value;
  if (!email || !password) return setMessage("loginMsg", "أدخل البريد الإلكتروني وكلمة المرور.", true);
  $("loginBtn").disabled = true; setMessage("loginMsg", "جارٍ تسجيل الدخول...");
  try {
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;
    if ((data.user?.email || "").toLowerCase() !== ADMIN_EMAIL.toLowerCase()) {
      await supabase.auth.signOut(); throw new Error("هذا الحساب غير مصرح له بإدارة المتجر.");
    }
    setMessage("loginMsg", "تم تسجيل الدخول."); await showSession(data.session);
  } catch (e) { setMessage("loginMsg", e.message || "تعذر تسجيل الدخول. تحقق من البيانات.", true); }
  finally { $("loginBtn").disabled = false; }
});

$("logout").addEventListener("click", async () => { await supabase.auth.signOut(); await showSession(null); });
supabase.auth.onAuthStateChange((_event, session) => { showSession(session); });

 document.querySelectorAll("nav button").forEach(button => button.addEventListener("click", () => {
  ["products", "orders"].forEach(view => $(view).classList.toggle("hide", view !== button.dataset.view));
}));

function resetForm() {
  $("form").reset(); $("pid").value = ""; currentImageUrl = ""; $("imageUrl").value = "";
  $("preview").removeAttribute("src"); $("preview").classList.add("hide"); $("active").checked = true;
  $("uploadMsg").textContent = "اختر صورة من هاتفك، وسيتم رفعها إلى Supabase عند حفظ المنتج.";
  setMessage("formMsg", "");
}
$("add").addEventListener("click", () => { resetForm(); $("form").classList.remove("hide"); });
$("cancel").addEventListener("click", () => $("form").classList.add("hide"));

$("imageFile").addEventListener("change", () => {
  const file = $("imageFile").files?.[0]; if (!file) return;
  if (!file.type.startsWith("image/")) { setMessage("formMsg", "اختر ملف صورة صالحاً.", true); $("imageFile").value = ""; return; }
  if (file.size > 5 * 1024 * 1024) { setMessage("formMsg", "حجم الصورة أكبر من 5 ميغابايت. اختر صورة أصغر.", true); $("imageFile").value = ""; return; }
  $("preview").src = URL.createObjectURL(file); $("preview").classList.remove("hide");
  $("uploadMsg").textContent = `تم اختيار ${file.name}؛ سترفع عند حفظ المنتج.`;
});

async function uploadProductImage(file) {
  // Upload through the authenticated Storage REST endpoint with a clear timeout.
  const { data: sessionData, error: sessionError } = await supabase.auth.getSession();
  if (sessionError) throw new Error(`تعذر قراءة جلسة الدخول: ${sessionError.message}`);
  const accessToken = sessionData.session?.access_token;
  if (!accessToken) throw new Error("انتهت جلسة المدير. سجّل الخروج ثم الدخول مجدداً.");
  const extFromName = (file.name.split(".").pop() || "jpg").toLowerCase().replace(/[^a-z0-9]/g, "");
  const extFromType = ({ "image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif" })[file.type];
  const ext = extFromType || extFromName || "jpg";
  const path = `${Date.now()}-${crypto.randomUUID()}.${ext}`;
  const endpoint = `${SUPABASE_URL}/storage/v1/object/products/${path}`;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 45000);
  let response;
  try {
    response = await fetch(endpoint, {
      method: "POST",
      headers: { "apikey": SUPABASE_PUBLISHABLE_KEY, "Authorization": `Bearer ${accessToken}`, "Content-Type": file.type || "image/jpeg", "x-upsert": "false", "cache-control": "3600" },
      body: file, signal: controller.signal
    });
  } catch (error) {
    if (error.name === "AbortError") throw new Error("انتهت مهلة رفع الصورة بعد 45 ثانية. جرّب صورة أصغر أو أعد المحاولة.");
    throw new Error(`تعذر الاتصال بخدمة رفع الصور: ${error.message || error}`);
  } finally { clearTimeout(timeout); }
  if (!response.ok) {
    let detail = "";
    try { const body = await response.json(); detail = body.message || body.error || JSON.stringify(body); }
    catch { detail = await response.text().catch(() => ""); }
    throw new Error(`فشل رفع الصورة (${response.status}): ${detail || response.statusText}`);
  }
  const { data } = supabase.storage.from("products").getPublicUrl(path);
  if (!data?.publicUrl) throw new Error("تم رفع الصورة لكن تعذر استخراج رابطها.");
  return data.publicUrl;
}

$("form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!currentUser) return setMessage("formMsg", "انتهت جلسة الدخول. سجّل الدخول مجدداً.", true);
  const saveButton = $("form").querySelector('button[type="submit"]'); saveButton.disabled = true;
  try {
    let imageUrl = currentImageUrl || $("imageUrl").value.trim();
    const file = $("imageFile").files?.[0];
    if (file) { $("uploadMsg").textContent = "جارٍ رفع الصورة إلى Supabase... لا تغلق الصفحة."; imageUrl = await uploadProductImage(file); }
    const record = {
      name: $("name").value.trim(), category: $("category").value,
      price: Number($("price").value), stock: Number($("stock").value),
      description: $("description").value.trim(), image_url: imageUrl || null,
      is_active: $("active").checked, updated_at: new Date().toISOString()
    };
    if (!record.name || !Number.isFinite(record.price) || !Number.isFinite(record.stock)) throw new Error("تحقق من اسم المنتج والسعر والكمية.");
    let result;
    if ($("pid").value) result = await supabase.from("products").update(record).eq("id", $("pid").value);
    else result = await supabase.from("products").insert(record);
    if (result.error) throw new Error(`تعذر حفظ المنتج: ${result.error.message}`);
    setMessage("formMsg", "تم حفظ المنتج بنجاح."); $("form").classList.add("hide"); resetForm(); await loadProducts();
  } catch (error) { setMessage("formMsg", error.message || "حدث خطأ أثناء الحفظ.", true); }
  finally { saveButton.disabled = false; }
});

function makeButton(label, action) { const b = document.createElement("button"); b.textContent = label; b.addEventListener("click", action); return b; }
async function loadProducts() {
  const container = $("productList"); container.textContent = "جارٍ تحميل المنتجات...";
  const { data, error } = await supabase.from("products").select("*").order("created_at", { ascending: false });
  if (error) { container.textContent = `تعذر تحميل المنتجات: ${error.message}`; return; }
  container.replaceChildren();
  if (!data?.length) { container.textContent = "لا توجد منتجات بعد."; return; }
  data.forEach(product => {
    const item = document.createElement("div"); item.className = "item";
    const img = document.createElement("img"); img.src = product.image_url || ""; img.alt = product.name || "";
    const info = document.createElement("div"); info.className = "info";
    info.textContent = `${product.name} — ${product.price} د.ل — المخزون: ${product.stock} — ${product.is_active ? "ظاهر" : "مخفي"}`;
    const edit = makeButton("تعديل", () => {
      resetForm(); $("pid").value = product.id; $("name").value = product.name || "";
      $("category").value = product.category || "هواتف"; $("price").value = product.price ?? 0;
      $("stock").value = product.stock ?? 0; $("description").value = product.description || "";
      currentImageUrl = product.image_url || ""; $("imageUrl").value = currentImageUrl;
      $("active").checked = product.is_active !== false;
      if (currentImageUrl) { $("preview").src = currentImageUrl; $("preview").classList.remove("hide"); }
      $("form").classList.remove("hide"); window.scrollTo({ top: 0, behavior: "smooth" });
    });
    const del = makeButton("حذف", async () => {
      if (!confirm("هل تريد حذف هذا المنتج؟")) return;
      const { error: deleteError } = await supabase.from("products").delete().eq("id", product.id);
      if (deleteError) alert(`تعذر الحذف: ${deleteError.message}`); else await loadProducts();
    });
    item.append(img, info, edit, del); container.append(item);
  });
}

async function loadOrders() {
  const container = $("orderList"); container.textContent = "جارٍ تحميل الطلبات...";
  const { data, error } = await supabase.from("orders").select("*").order("created_at", { ascending: false }).limit(100);
  if (error) { container.textContent = `قسم الطلبات جاهز، لكن تعذر تحميلها: ${error.message}`; return; }
  container.replaceChildren();
  if (!data?.length) { container.textContent = "لا توجد طلبات حالياً."; return; }
  data.forEach(order => { const p = document.createElement("p"); p.textContent = `طلب ${order.id} — الحالة: ${order.status || "جديد"} — الإجمالي: ${order.total ?? "—"} د.ل`; container.append(p); });
}

const { data: initial } = await supabase.auth.getSession(); await showSession(initial.session);
      
