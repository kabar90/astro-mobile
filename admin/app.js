import { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm";

import {
  SUPABASE_URL,
  SUPABASE_PUBLISHABLE_KEY,
  ADMIN_EMAIL,
  FIREBASE_CONFIG,
  FIREBASE_VAPID_KEY
} from "./supabase-config.js";

import { initializeApp, getApps } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-app.js";

import {
  getMessaging,
  getToken,
  isSupported
} from "https://www.gstatic.com/firebasejs/10.13.2/firebase-messaging.js";

// ========================================
// الاتصال بقاعدة بيانات Supabase
// ========================================

const supabase = createClient(
  SUPABASE_URL,
  SUPABASE_PUBLISHABLE_KEY
);

window.supabaseClient = supabase;
window.sb = supabase;

const $ = (id) => document.getElementById(id);

let currentUser = null;
let currentImageUrl = "";

// ========================================
// Firebase - إشعارات متصفح المدير
// ========================================

let firebaseMessaging = null;

function initializeFirebaseMessaging() {
  if (!FIREBASE_CONFIG || !FIREBASE_VAPID_KEY) {
    throw new Error("إعدادات Firebase غير موجودة في supabase-config.js");
  }

  const firebaseApp = getApps().length
    ? getApps()[0]
    : initializeApp(FIREBASE_CONFIG);

  firebaseMessaging = getMessaging(firebaseApp);

  return firebaseMessaging;
}

// إنشاء زر تفعيل إشعارات المتصفح
function createBrowserNotificationButton() {
  if ($("astroEnableBrowserNotifications")) return;

  const button = document.createElement("button");

  button.id = "astroEnableBrowserNotifications";
  button.type = "button";
  button.textContent = "تفعيل إشعارات الطلبات على هذا المتصفح";

  button.style.cssText = `
    display:block;
    width:100%;
    margin:12px 0;
    padding:13px;
    border:0;
    border-radius:10px;
    background:#16734a;
    color:white;
    font-size:15px;
    font-weight:bold;
    cursor:pointer;
  `;

  const message = document.createElement("p");
  message.id = "astroBrowserNotificationMsg";
  message.setAttribute("role", "status");

  const dash = $("dash");

  if (dash) {
    dash.insertBefore(button, dash.firstChild);
    dash.insertBefore(message, button.nextSibling);
  }

  button.addEventListener("click", registerAdminBrowser);
}

// عرض رسالة حالة إشعارات المتصفح
function showBrowserMessage(message, error = false) {
  const element = $("astroBrowserNotificationMsg");

  if (!element) return;

  element.textContent = message;
  element.style.color = error ? "#b42318" : "#16734a";
}

// تسجيل المتصفح وحفظ رمز Firebase في جدول الإدارة
async function registerAdminBrowser() {
  const button = $("astroEnableBrowserNotifications");

  if (!currentUser) {
    showBrowserMessage("يرجى تسجيل الدخول بحساب المدير.", true);
    return;
  }

  if (!("Notification" in window)) {
    showBrowserMessage(
      "هذا المتصفح لا يدعم إشعارات الويب.",
      true
    );
    return;
  }

  if (!("serviceWorker" in navigator)) {
    showBrowserMessage(
      "المتصفح لا يدعم خدمة الإشعارات المطلوبة.",
      true
    );
    return;
  }

  if (button) {
    button.disabled = true;
    button.textContent = "جارٍ تفعيل الإشعارات...";
  }

  try {
    const supported = await isSupported();

    if (!supported) {
      throw new Error(
        "إشعارات Firebase غير مدعومة في هذا المتصفح."
      );
    }

    const permission = await Notification.requestPermission();

    if (permission !== "granted") {
      throw new Error(
        "لم تسمح للمتصفح بإرسال الإشعارات."
      );
    }

    initializeFirebaseMessaging();

    const registration = await navigator.serviceWorker.register(
      "./firebase-messaging-sw.js",
      {
        scope: "./"
      }
    );

    await navigator.serviceWorker.ready;

    const token = await getToken(firebaseMessaging, {
      vapidKey: FIREBASE_VAPID_KEY,
      serviceWorkerRegistration: registration
    });

    if (!token) {
      throw new Error(
        "لم يتم الحصول على رمز جهاز المتصفح من Firebase."
      );
    }

    const { error } = await supabase
      .from("astro_admin_device_tokens")
      .upsert(
        {
          token,
          platform: "web",
          admin_email: currentUser.email.toLowerCase(),
          updated_at: new Date().toISOString()
        },
        {
          onConflict: "token"
        }
      );

    if (error) throw error;

    showBrowserMessage(
      "تم تفعيل إشعارات الطلبات لهذا المتصفح وحفظ الجهاز بنجاح."
    );

    if (button) {
      button.textContent = "تم تفعيل إشعارات هذا المتصفح";
    }

  } catch (error) {
    console.error("ASTRO browser notifications:", error);

    showBrowserMessage(
      `تعذر تفعيل الإشعارات: ${error.message || error}`,
      true
    );

    if (button) {
      button.textContent = "إعادة محاولة تفعيل الإشعارات";
    }

  } finally {
    if (button) button.disabled = false;
  }
}

// ========================================
// الرسائل العامة
// ========================================

const setMessage = (id, message, error = false) => {
  const el = $(id);
  if (!el) return;

  el.textContent = message;
  el.style.color = error ? "#b42318" : "#16734a";
};

// ========================================
// التحقق من المدير وإدارة الجلسة
// ========================================

async function showSession(session) {
  const user = session?.user;

  if (
    user &&
    (user.email || "").toLowerCase() === ADMIN_EMAIL.toLowerCase()
  ) {
    currentUser = user;

    $("login")?.classList.add("hide");
    $("dash")?.classList.remove("hide");
    $("logout")?.classList.remove("hide");

    createBrowserNotificationButton();

    await Promise.all([
      loadProducts(),
      loadOrders()
    ]);

    if (window.ASTRONotifications?.refresh) {
      await window.ASTRONotifications.refresh();
    }

  } else {
    currentUser = null;

    if (user) {
      await supabase.auth.signOut();
    }

    $("login")?.classList.remove("hide");
    $("dash")?.classList.add("hide");
    $("logout")?.classList.add("hide");
  }
}

// ========================================
// تسجيل الدخول
// ========================================

$("loginBtn")?.addEventListener("click", async () => {
  const email = $("email")?.value.trim();
  const password = $("password")?.value;

  if (!email || !password) {
    return setMessage(
      "loginMsg",
      "أدخل البريد الإلكتروني وكلمة المرور.",
      true
    );
  }

  $("loginBtn").disabled = true;
  setMessage("loginMsg", "جارٍ تسجيل الدخول...");

  try {
    const { data, error } =
      await supabase.auth.signInWithPassword({
        email,
        password
      });

    if (error) throw error;

    if (
      (data.user?.email || "").toLowerCase() !==
      ADMIN_EMAIL.toLowerCase()
    ) {
      await supabase.auth.signOut();

      throw new Error(
        "هذا الحساب غير مصرح له بإدارة المتجر."
      );
    }

    setMessage("loginMsg", "تم تسجيل الدخول بنجاح.");

    await showSession(data.session);

  } catch (error) {
    setMessage(
      "loginMsg",
      error.message || "تعذر تسجيل الدخول.",
      true
    );
  } finally {
    $("loginBtn").disabled = false;
  }
});

// ========================================
// تسجيل الخروج
// ========================================

$("logout")?.addEventListener("click", async () => {
  await supabase.auth.signOut();
  await showSession(null);
});

// متابعة تغييرات الجلسة
supabase.auth.onAuthStateChange((_event, session) => {
  showSession(session);
});

// ========================================
// التنقل بين أقسام لوحة التحكم
// ========================================

document.querySelectorAll("nav button").forEach(button => {
  button.addEventListener("click", async () => {

    const views = [
      "products",
      "orders",
      "bank",
      "notifications",
      "history"
    ];

    views.forEach(view => {
      const section = $(view);

      if (section) {
        section.classList.toggle(
          "hide",
          view !== button.dataset.view
        );
      }
    });

    if (button.dataset.view === "products") {
      await loadProducts();
    }

    if (button.dataset.view === "orders") {
      await loadOrders();
    }

    if (
      button.dataset.view === "notifications" ||
      button.dataset.view === "history"
    ) {
      await window.ASTRONotifications?.refresh?.();
    }
  });
});

// ========================================
// إرسال إشعار ترويجي للعملاء
// ========================================

$("promoForm")?.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!currentUser) {
    return setMessage(
      "promoMsg",
      "انتهت جلسة المدير. سجّل الدخول مجدداً.",
      true
    );
  }

  const title = $("promoTitle")?.value.trim();
  const body = $("promoBody")?.value.trim();

  if (!title || !body) {
    return setMessage(
      "promoMsg",
      "اكتب عنوان الإشعار ونص الرسالة.",
      true
    );
  }

  if (
    !confirm(
      "هل تريد إرسال هذا الإشعار إلى جميع العملاء المسجلين؟"
    )
  ) {
    return;
  }

  const sendButton = $("sendPromo");

  if (sendButton) sendButton.disabled = true;

  setMessage("promoMsg", "جارٍ إرسال الإشعار...");

  try {
    const { error } = await supabase.rpc(
      "send_promo_notification",
      {
        p_title: title,
        p_body: body
      }
    );

    if (error) throw error;

    setMessage(
      "promoMsg",
      "تم تسجيل طلب الإرسال بنجاح."
    );

    $("promoForm")?.reset();

    await window.ASTRONotifications?.refresh?.();

  } catch (error) {
    setMessage(
      "promoMsg",
      `تعذر إرسال الإشعار: ${error.message || error}`,
      true
    );
  } finally {
    if (sendButton) sendButton.disabled = false;
  }
});

// ========================================
// إعادة ضبط نموذج المنتج
// ========================================

function resetForm() {
  const form = $("form");
  if (!form) return;

  form.reset();

  $("pid").value = "";
  $("colors").value = "";

  currentImageUrl = "";

  $("imageUrl").value = "";
  $("imageFile").value = "";

  $("preview").removeAttribute("src");
  $("preview").classList.add("hide");

  $("active").checked = true;

  $("uploadMsg").textContent =
    "اختر صورة من هاتفك، وسيتم رفعها إلى Supabase عند حفظ المنتج.";

  setMessage("formMsg", "");
}

// ========================================
// إضافة منتج
// ========================================

$("add")?.addEventListener("click", () => {
  resetForm();
  $("form")?.classList.remove("hide");
});

// ========================================
// إلغاء إضافة المنتج
// ========================================

$("cancel")?.addEventListener("click", () => {
  $("form")?.classList.add("hide");
});

// ========================================
// اختيار صورة المنتج
// ========================================

$("imageFile")?.addEventListener("change", () => {
  const file = $("imageFile").files?.[0];

  if (!file) return;

  if (!file.type.startsWith("image/")) {
    setMessage(
      "formMsg",
      "اختر ملف صورة صالحاً.",
      true
    );

    $("imageFile").value = "";
    return;
  }

  if (file.size > 5 * 1024 * 1024) {
    setMessage(
      "formMsg",
      "حجم الصورة أكبر من 5 ميغابايت. اختر صورة أصغر.",
      true
    );

    $("imageFile").value = "";
    return;
  }

  $("preview").src = URL.createObjectURL(file);
  $("preview").classList.remove("hide");

  $("uploadMsg").textContent =
    `تم اختيار ${file.name}؛ سترفع عند حفظ المنتج.`;
});

// ========================================
// رفع صورة المنتج إلى Supabase
// ========================================

async function uploadProductImage(file) {
  const {
    data: sessionData,
    error: sessionError
  } = await supabase.auth.getSession();

  if (sessionError) {
    throw new Error(
      `تعذر قراءة جلسة الدخول: ${sessionError.message}`
    );
  }

  const accessToken = sessionData.session?.access_token;

  if (!accessToken) {
    throw new Error(
      "انتهت جلسة المدير. سجّل الدخول مجدداً."
    );
  }

  const extFromName = (
    file.name.split(".").pop() || "jpg"
  ).toLowerCase().replace(/[^a-z0-9]/g, "");

  const extFromType = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif"
  }[file.type];

  const ext = extFromType || extFromName || "jpg";

  const path =
    `${Date.now()}-${crypto.randomUUID()}.${ext}`;

  const endpoint =
    `${SUPABASE_URL}/storage/v1/object/products/${path}`;

  const controller = new AbortController();

  const timeout = setTimeout(
    () => controller.abort(),
    45000
  );

  let response;

  try {
    response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "apikey": SUPABASE_PUBLISHABLE_KEY,
        "Authorization": `Bearer ${accessToken}`,
        "Content-Type": file.type || "image/jpeg",
        "x-upsert": "false",
        "cache-control": "3600"
      },
      body: file,
      signal: controller.signal
    });

  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error(
        "انتهت مهلة رفع الصورة بعد 45 ثانية."
      );
    }

    throw new Error(
      `تعذر الاتصال بخدمة رفع الصور: ${error.message || error}`
    );

  } finally {
    clearTimeout(timeout);
  }

  if (!response.ok) {
    let detail = "";

    try {
      const body = await response.json();

      detail =
        body.message ||
        body.error ||
        JSON.stringify(body);

    } catch {
      detail = await response.text().catch(() => "");
    }

    throw new Error(
      `فشل رفع الصورة (${response.status}): ${detail || response.statusText}`
    );
  }

  const { data } = supabase
    .storage
    .from("products")
    .getPublicUrl(path);

  if (!data?.publicUrl) {
    throw new Error(
      "تم رفع الصورة لكن تعذر استخراج رابطها."
    );
  }

  return data.publicUrl;
}

// ========================================
// حفظ المنتج أو تعديله
// ========================================

$("form")?.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!currentUser) {
    return setMessage(
      "formMsg",
      "انتهت جلسة الدخول. سجّل الدخول مجدداً.",
      true
    );
  }

  const saveButton =
    $("form").querySelector('button[type="submit"]');

  if (saveButton) saveButton.disabled = true;

  try {
    let imageUrl =
      currentImageUrl || $("imageUrl").value.trim();

    const file = $("imageFile").files?.[0];

    if (file) {
      $("uploadMsg").textContent =
        "جارٍ رفع الصورة إلى Supabase... لا تغلق الصفحة.";

      imageUrl = await uploadProductImage(file);

      $("imageUrl").value = imageUrl;
    }

    const colors = $("colors").value
      .split(/[,،\n]/)
      .map(color => color.trim())
      .filter(Boolean);

    const record = {
      name: $("name").value.trim(),
      category: $("category").value,
      price: Number($("price").value),
      stock: Number($("stock").value),
      description: $("description").value.trim(),
      colors: colors,
      image_url: imageUrl || null,
      is_active: $("active").checked,
      updated_at: new Date().toISOString()
    };

    if (
      !record.name ||
      !Number.isFinite(record.price) ||
      !Number.isFinite(record.stock) ||
      record.price < 0 ||
      record.stock < 0
    ) {
      throw new Error(
        "تحقق من اسم المنتج والسعر والكمية."
      );
    }

    let result;

    if ($("pid").value) {
      result = await supabase
        .from("products")
        .update(record)
        .eq("id", $("pid").value);
    } else {
      result = await supabase
        .from("products")
        .insert(record);
    }

    if (result.error) {
      throw new Error(
        `تعذر حفظ المنتج: ${result.error.message}`
      );
    }

    setMessage(
      "formMsg",
      "تم حفظ المنتج بنجاح."
    );

    $("form").classList.add("hide");

    resetForm();

    await loadProducts();

  } catch (error) {
    setMessage(
      "formMsg",
      error.message || "حدث خطأ أثناء الحفظ.",
      true
    );
  } finally {
    if (saveButton) saveButton.disabled = false;
  }
});

// ========================================
// إنشاء الأزرار
// ========================================

function makeButton(label, action) {
  const button = document.createElement("button");

  button.type = "button";
  button.textContent = label;

  button.addEventListener("click", action);

  return button;
}

// ========================================
// تحميل المنتجات
// ========================================

async function loadProducts() {
  const container = $("productList");

  if (!container) return;

  container.textContent = "جارٍ تحميل المنتجات...";

  const { data, error } = await supabase
    .from("products")
    .select("*")
    .order("created_at", { ascending: false });

  if (error) {
    container.textContent =
      `تعذر تحميل المنتجات: ${error.message}`;
    return;
  }

  container.replaceChildren();

  if (!data?.length) {
    container.textContent = "لا توجد منتجات بعد.";
    return;
  }

  data.forEach(product => {
    const item = document.createElement("div");
    item.className = "item";

    const img = document.createElement("img");

    img.src = product.image_url || "";
    img.alt = product.name || "";

    const info = document.createElement("div");
    info.className = "info";

    const colorsText = Array.isArray(product.colors)
      ? product.colors.join("، ")
      : "";

    info.textContent =
      `${product.name} — ${product.price} د.ل — المخزون: ${product.stock} — الألوان: ${colorsText || "غير محددة"} — ${product.is_active ? "ظاهر" : "مخفي"}`;

    const edit = makeButton("تعديل", () => {
      resetForm();

      $("pid").value = product.id;
      $("name").value = product.name || "";
      $("category").value = product.category || "هواتف";
      $("price").value = product.price ?? 0;
      $("stock").value = product.stock ?? 0;
      $("description").value = product.description || "";

      $("colors").value = Array.isArray(product.colors)
        ? product.colors.join("، ")
        : "";

      currentImageUrl = product.image_url || "";
      $("imageUrl").value = currentImageUrl;

      $("active").checked = product.is_active !== false;

      if (currentImageUrl) {
        $("preview").src = currentImageUrl;
        $("preview").classList.remove("hide");
      }

      $("form").classList.remove("hide");

      window.scrollTo({
        top: 0,
        behavior: "smooth"
      });
    });

    const del = makeButton("حذف", async () => {
      if (!confirm("هل تريد حذف هذا المنتج؟")) return;

      const { error: deleteError } = await supabase
        .from("products")
        .delete()
        .eq("id", product.id);

      if (deleteError) {
        alert(`تعذر الحذف: ${deleteError.message}`);
      } else {
        await loadProducts();
      }
    });

    item.append(img, info, edit, del);

    container.append(item);
  });
}

// ========================================
// تحميل الطلبات
// ========================================

async function loadOrders() {
  const container = $("orderList");

  if (!container) return;

  container.textContent = "جارٍ تحميل الطلبات...";

  const { data, error } = await supabase
    .from("orders")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(100);

  if (error) {
    container.textContent =
      `تعذر تحميل الطلبات: ${error.message}`;
    return;
  }

  container.replaceChildren();

  if (!data?.length) {
    container.textContent = "لا توجد طلبات حالياً.";
    return;
  }

  data.forEach(order => {
    const p = document.createElement("p");

    p.textContent =
      `طلب ${order.id} — الحالة: ${order.status || "جديد"} — الإجمالي: ${order.total_price ?? order.total ?? "—"} د.ل`;

    container.append(p);
  });
}

// ========================================
// استعادة جلسة المدير عند فتح الصفحة
// ========================================

const { data: initial, error: initialError } =
  await supabase.auth.getSession();

if (initialError) {
  setMessage(
    "loginMsg",
    initialError.message,
         true
    );
  } else {
    await showSession(initial.session);
}
