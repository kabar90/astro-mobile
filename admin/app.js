
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

  // منع تنفيذ تحميل لوحة التحكم مرتين لنفس جلسة المدير
  if (user && currentUser?.id === user.id) return;

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
      loadCategories(),
      loadProducts(),
      loadOrders(),
      loadDeliveryCities()
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
    // onAuthStateChange يتولى تحديث واجهة لوحة التحكم بعد نجاح الدخول

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
  const { error } = await supabase.auth.signOut();
  if (error) {
    setMessage("loginMsg", `تعذر تسجيل الخروج: ${error.message}`, true);
  }
});

// متابعة تغييرات الجلسة خارج قفل مصادقة Supabase
supabase.auth.onAuthStateChange((_event, session) => {
  setTimeout(() => {
    showSession(session).catch(error => {
      console.error("ASTRO session error:", error);
      setMessage("loginMsg", error.message || "تعذر تحميل لوحة التحكم.", true);
    });
  }, 0);
});


// ========================================
// إعدادات طريقة عرض الأقسام
// ========================================

const CATEGORY_DISPLAY_DEFAULTS = {
  id: 1,
  main_layout: "grid_2",
  subcategory_layout: "grid"
};

async function loadCategoryDisplaySettings() {
  const mainSelect = $("mainCategoryLayout");
  const subSelect = $("subcategoryLayout");
  if (!mainSelect || !subSelect) return;

  setMessage("categoryDisplaySettingsMsg", "جارٍ تحميل إعدادات عرض الأقسام...");

  try {
    const { data, error } = await supabase
      .from("category_display_settings")
      .select("id,main_layout,subcategory_layout")
      .eq("id", 1)
      .maybeSingle();

    if (error) throw error;

    const settings = data || CATEGORY_DISPLAY_DEFAULTS;
    mainSelect.value = ["grid_2", "grid_3", "horizontal"].includes(settings.main_layout)
      ? settings.main_layout
      : CATEGORY_DISPLAY_DEFAULTS.main_layout;
    subSelect.value = ["grid", "horizontal"].includes(settings.subcategory_layout)
      ? settings.subcategory_layout
      : CATEGORY_DISPLAY_DEFAULTS.subcategory_layout;

    setMessage(
      "categoryDisplaySettingsMsg",
      data ? "تم تحميل إعدادات عرض الأقسام." : "لم تُحفظ إعدادات بعد؛ يتم عرض القيم الافتراضية."
    );
  } catch (error) {
    console.error("ASTRO category display settings load error:", error);
    setMessage(
      "categoryDisplaySettingsMsg",
      `تعذر تحميل الإعدادات: ${error.message || error}`,
      true
    );
  }
}

async function saveCategoryDisplaySettings() {
  if (!currentUser) {
    return setMessage(
      "categoryDisplaySettingsMsg",
      "انتهت جلسة المدير. سجّل الدخول مجدداً.",
      true
    );
  }

  const mainLayout = $("mainCategoryLayout")?.value;
  const subcategoryLayout = $("subcategoryLayout")?.value;

  if (!["grid_2", "grid_3", "horizontal"].includes(mainLayout)) {
    return setMessage("categoryDisplaySettingsMsg", "اختر طريقة عرض صحيحة للأقسام الرئيسية.", true);
  }

  if (!["grid", "horizontal"].includes(subcategoryLayout)) {
    return setMessage("categoryDisplaySettingsMsg", "اختر طريقة عرض صحيحة للأقسام الفرعية.", true);
  }

  const button = $("saveCategoryDisplaySettings");
  if (button) button.disabled = true;
  setMessage("categoryDisplaySettingsMsg", "جارٍ حفظ إعدادات عرض الأقسام...");

  try {
    const { error } = await supabase
      .from("category_display_settings")
      .upsert({
        id: 1,
        main_layout: mainLayout,
        subcategory_layout: subcategoryLayout,
        updated_at: new Date().toISOString()
      }, { onConflict: "id" });

    if (error) throw error;

    setMessage("categoryDisplaySettingsMsg", "تم حفظ إعدادات عرض الأقسام بنجاح.");
  } catch (error) {
    console.error("ASTRO category display settings save error:", error);
    setMessage(
      "categoryDisplaySettingsMsg",
      `تعذر حفظ الإعدادات: ${error.message || error}`,
      true
    );
  } finally {
    if (button) button.disabled = false;
  }
}

$("saveCategoryDisplaySettings")?.addEventListener("click", saveCategoryDisplaySettings);
$("refreshCategoryDisplaySettings")?.addEventListener("click", loadCategoryDisplaySettings);

// ========================================
// إعدادات صفحة تواصل معنا
// ========================================
const CONTACT_DEFAULT_ADDRESS = "طرابلس، أبوسليم، شارع أم درمان الرئيسي، بالقرب من شارع السلام";

async function loadStoreContact() {
  setMessage("storeContactMsg", "جارٍ تحميل بيانات التواصل...");
  try {
    const { data, error } = await supabase.from("store_contact_settings")
      .select("id,address,phone,whatsapp,facebook_url,instagram_url,tiktok_url,working_hours")
      .eq("id", 1).maybeSingle();
    if (error) throw error;
    const row = data || {};
    $("contactAddress").value = row.address || CONTACT_DEFAULT_ADDRESS;
    $("contactPhone").value = row.phone || "";
    $("contactWhatsapp").value = row.whatsapp || "";
    $("contactFacebook").value = row.facebook_url || "";
    $("contactInstagram").value = row.instagram_url || "";
    $("contactTiktok").value = row.tiktok_url || "";
    $("contactHours").value = row.working_hours || "";
    setMessage("storeContactMsg", "تم تحميل بيانات التواصل.");
  } catch (error) {
    console.error("ASTRO contact settings load error:", error);
    setMessage("storeContactMsg", `تعذر تحميل البيانات: ${error.message || error}`, true);
  }
}

async function saveStoreContact() {
  if (!currentUser) return setMessage("storeContactMsg", "سجّل الدخول مجدداً.", true);
  const button = $("saveStoreContact");
  button.disabled = true;
  setMessage("storeContactMsg", "جارٍ حفظ البيانات...");
  try {
    const payload = {
      id: 1,
      address: $("contactAddress").value.trim(),
      phone: $("contactPhone").value.trim(),
      whatsapp: $("contactWhatsapp").value.trim(),
      facebook_url: $("contactFacebook").value.trim(),
      instagram_url: $("contactInstagram").value.trim(),
      tiktok_url: $("contactTiktok").value.trim(),
      working_hours: $("contactHours").value.trim(),
      updated_at: new Date().toISOString()
    };
    const { error } = await supabase.from("store_contact_settings").upsert(payload, { onConflict: "id" });
    if (error) throw error;
    setMessage("storeContactMsg", "تم حفظ بيانات التواصل بنجاح.");
  } catch (error) {
    console.error("ASTRO contact settings save error:", error);
    setMessage("storeContactMsg", `تعذر حفظ البيانات: ${error.message || error}`, true);
  } finally { button.disabled = false; }
}

$("saveStoreContact")?.addEventListener("click", saveStoreContact);
$("refreshStoreContact")?.addEventListener("click", loadStoreContact);

// ========================================
// التنقل بين أقسام لوحة التحكم
// ========================================

document.querySelectorAll("nav button").forEach(button => {
  button.addEventListener("click", async () => {

    const views = [
      "products",
      "categories",
      "offers",
      "orders",
      "delivery",
      "bank",
      "categoryDisplaySettings",
      "storeContact",
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

    if (button.dataset.view === "categories") {
      await loadCategories();
    }

    if (button.dataset.view === "orders") {
      await loadOrders();
    }

    if (button.dataset.view === "delivery") {
      await loadDeliveryCities();
    }

    if (button.dataset.view === "categoryDisplaySettings") {
      await loadCategoryDisplaySettings();
    }

    if (button.dataset.view === "storeContact") {
      await loadStoreContact();
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

  if ($("rewardEnabled")) $("rewardEnabled").checked = false;
  if ($("rewardPoints")) $("rewardPoints").value = "0";

  $("uploadMsg").textContent =
    "اختر صورة من هاتفك، وسيتم رفعها إلى Supabase عند حفظ المنتج.";

  setMessage("formMsg", "");

  if ($("subcategory")) {
    $("subcategory").replaceChildren(new Option("اختر القسم الرئيسي أولاً", ""));
    $("subcategory").disabled = true;
  }
}

// ========================================
// إضافة منتج
// ========================================

$("add")?.addEventListener("click", async () => {
  await loadCategories();
  resetForm();
  renderCategoryOptions();
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

    const rewardEnabled = $("rewardEnabled")?.checked === true;
    const rewardPointsInput = $("rewardPoints")?.value ?? "0";
    const rewardPoints = rewardEnabled ? Number(rewardPointsInput) : 0;

    if (!Number.isInteger(rewardPoints) || rewardPoints < 0) {
      throw new Error("أدخل عدداً صحيحاً من نقاط المكافآت لا يقل عن صفر.");
    }

    const record = {
      name: $("name").value.trim(),
      category: $("category").value,
      subcategory_id: $("subcategory").value || null,
      price: Number($("price").value),
      stock: Number($("stock").value),
      reward_points: rewardPoints,
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
// إدارة أقسام المتجر
// ========================================

let cachedCategories = [];
let editingCategoryId = null;
let currentCategoryImageUrl = "";
let categoryImagePreviewObjectUrl = "";

function getCategoryById(id) {
  return cachedCategories.find(category => String(category.id) === String(id));
}

function getDescendantCategoryIds(categoryId) {
  const found = new Set([String(categoryId)]);
  let changed = true;
  while (changed) {
    changed = false;
    cachedCategories.forEach(category => {
      if (category.parent_id != null && found.has(String(category.parent_id)) && !found.has(String(category.id))) {
        found.add(String(category.id));
        changed = true;
      }
    });
  }
  return found;
}

function renderCategoryOptions(selectedValue = $("category")?.value || "", selectedSubcategoryId = $("subcategory")?.value || "") {
  const select = $("category");
  if (!select) return;
  select.replaceChildren();

  const placeholder = document.createElement("option");
  placeholder.value = "";
  placeholder.textContent = cachedCategories.some(item => item.is_active && !item.parent_id)
    ? "اختر القسم الرئيسي"
    : "لا توجد أقسام رئيسية نشطة؛ أضف قسماً أولاً";
  select.append(placeholder);

  cachedCategories
    .filter(category => !category.parent_id && category.is_active)
    .forEach(category => {
      const option = document.createElement("option");
      option.value = category.name;
      option.dataset.categoryId = category.id;
      option.textContent = category.name;
      select.append(option);
    });

  if (selectedValue && !Array.from(select.options).some(option => option.value === selectedValue)) {
    const legacyOption = document.createElement("option");
    legacyOption.value = selectedValue;
    legacyOption.textContent = `${selectedValue} (قديم/متوقف)`;
    select.append(legacyOption);
  }
  if (selectedValue) select.value = selectedValue;

  renderProductSubcategoryOptions(selectedSubcategoryId);
}

function renderProductSubcategoryOptions(selectedSubcategoryId = $("subcategory")?.value || "") {
  const select = $("subcategory");
  const parentSelect = $("category");
  if (!select || !parentSelect) return;

    const parent = cachedCategories.find(category =>
      !category.parent_id && category.name === parentSelect.value
  );

  select.replaceChildren();
    const placeholder = document.createElement("option");
  placeholder.value = "";
  placeholder.textContent = parent ? "بدون قسم فرعي" : "اختر القسم الرئيسي أولاً";
  select.append(placeholder);

  if (!parent) {
    select.disabled = true;
    return;
  }

  const children = cachedCategories
    .filter(category => String(category.parent_id) === String(parent.id) && category.is_active)
    .sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0) || a.name.localeCompare(b.name, "ar"));

  children.forEach(category => {
    const option = document.createElement("option");
    option.value = category.id;
    option.textContent = category.name;
    select.append(option);
  });

  const selected = getCategoryById(selectedSubcategoryId);
  if (selected && String(selected.parent_id) === String(parent.id) &&
      !Array.from(select.options).some(option => option.value === String(selected.id))) {
    const legacyOption = document.createElement("option");
    legacyOption.value = selected.id;
    legacyOption.textContent = `${selected.name} (متوقف)`;
    select.append(legacyOption);
  }

  select.disabled = children.length === 0 && !selectedSubcategoryId;
  if (selectedSubcategoryId) select.value = String(selectedSubcategoryId);
}

function renderCategoryParentOptions(selectedParentId = "") {
  const select = $("categoryParent");
  if (!select) return;
  select.replaceChildren();

  const rootOption = document.createElement("option");
  rootOption.value = "";
  rootOption.textContent = "قسم رئيسي (بدون قسم أب)";
  select.append(rootOption);

  const excluded = editingCategoryId !== null
    ? getDescendantCategoryIds(editingCategoryId)
    : new Set();

  cachedCategories
    .filter(category => !excluded.has(String(category.id)) && !category.parent_id)
    .sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0) || a.name.localeCompare(b.name, "ar"))
    .forEach(category => {
      const option = document.createElement("option");
      option.value = category.id;
      option.textContent = category.name;
      select.append(option);
    });

  if (selectedParentId) select.value = String(selectedParentId);
}

function setCategoryImagePreview(url = "") {
  const preview = $("categoryImagePreview");
  if (!preview) return;
  if (url) {
    preview.src = url;
    preview.classList.remove("hide");
  } else {
    preview.removeAttribute("src");
    preview.classList.add("hide");
  }
}

function resetCategoryImageSelection() {
  currentCategoryImageUrl = "";
  if ($("categoryImageFile")) $("categoryImageFile").value = "";
  if (categoryImagePreviewObjectUrl) {
    URL.revokeObjectURL(categoryImagePreviewObjectUrl);
    categoryImagePreviewObjectUrl = "";
  }
  setCategoryImagePreview("");
  $("clearCategoryImage")?.classList.add("hide");
  setMessage("categoryImageMsg", "اختر صورة للقسم الرئيسي أو الفرعي.");
}

function resetCategoryForm() {
  editingCategoryId = null;
  $("categoryForm")?.reset();
  resetCategoryImageSelection();
  if ($("categoryOrder")) $("categoryOrder").value = "0";
  if ($("categoryActive")) $("categoryActive").checked = true;
  renderCategoryParentOptions();
  if ($("saveCategory")) $("saveCategory").textContent = "إضافة القسم";
  $("cancelCategoryEdit")?.classList.add("hide");
  setMessage("categoryMsg", "");
}

// اختيار ومعاينة صورة القسم قبل رفعها
$("categoryImageFile")?.addEventListener("change", () => {
  const file = $("categoryImageFile").files?.[0];
  if (!file) return;

  if (!file.type.startsWith("image/")) {
    $("categoryImageFile").value = "";
    return setMessage("categoryImageMsg", "اختر ملف صورة صالحاً.", true);
  }
  if (file.size > 5 * 1024 * 1024) {
    $("categoryImageFile").value = "";
    return setMessage("categoryImageMsg", "حجم الصورة أكبر من 5 ميغابايت. اختر صورة أصغر.", true);
  }

  if (categoryImagePreviewObjectUrl) URL.revokeObjectURL(categoryImagePreviewObjectUrl);
  categoryImagePreviewObjectUrl = URL.createObjectURL(file);
  setCategoryImagePreview(categoryImagePreviewObjectUrl);
  $("clearCategoryImage")?.classList.remove("hide");
  setMessage("categoryImageMsg", `تم اختيار ${file.name}؛ سترفع عند حفظ القسم.`);
});

$("clearCategoryImage")?.addEventListener("click", () => {
  resetCategoryImageSelection();
  setMessage("categoryImageMsg", "ستُحفظ بيانات القسم بدون صورة عند الضغط على حفظ.");
});

// رفع صورة القسم داخل مجلد categories في bucket المنتجات الحالي
async function uploadCategoryImage(file) {
  const extFromType = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif"
  }[file.type];
  const extFromName = (file.name.split(".").pop() || "jpg")
    .toLowerCase().replace(/[^a-z0-9]/g, "");
  const ext = extFromType || extFromName || "jpg";
  const path = `categories/${Date.now()}-${crypto.randomUUID()}.${ext}`;

  const { error } = await supabase.storage
    .from("products")
    .upload(path, file, {
      contentType: file.type || "image/jpeg",
      cacheControl: "3600",
      upsert: false
    });
  if (error) throw new Error(`تعذر رفع صورة القسم: ${error.message}`);

  const { data } = supabase.storage.from("products").getPublicUrl(path);
  if (!data?.publicUrl) throw new Error("تم رفع الصورة لكن تعذر استخراج رابطها.");
  return data.publicUrl;
}

function renderCategoryList() {
  const container = $("categoryList");
  if (!container) return;
  container.replaceChildren();

  if (!cachedCategories.length) {
    container.textContent = "لا توجد أقسام حالياً. أضف أول قسم من النموذج أعلاه.";
    return;
  }

  const search = $("categorySearch")?.value.trim().toLocaleLowerCase() || "";
  const status = $("categoryStatusFilter")?.value || "all";
  const matches = category => {
    const text = [category.name, getCategoryById(category.parent_id)?.name || ""].join(" ").toLocaleLowerCase();
    return (!search || text.includes(search)) &&
      (status === "all" || (status === "active" ? category.is_active : !category.is_active));
  };
  const visible = cachedCategories.filter(matches);
  const countLabel = $("categoryFilterStatus");
  if (countLabel) countLabel.textContent = `عدد النتائج: ${visible.length} من أصل ${cachedCategories.length}`;

  const roots = visible
    .filter(category => !category.parent_id)
    .sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0) || a.name.localeCompare(b.name, "ar"));

  roots.forEach(parent => {
    const parentRow = document.createElement("div");
    parentRow.className = "item category-parent-item";

    const parentInfo = document.createElement("div");
    parentInfo.className = "info";
    parentInfo.textContent = `📁 ${parent.name} — قسم رئيسي — الترتيب: ${parent.sort_order ?? 0} — ${parent.is_active ? "نشط" : "متوقف"}`;
    if (parent.image_url) {
      const image = document.createElement("img");
      image.src = parent.image_url;
      image.alt = `صورة ${parent.name}`;
      image.loading = "lazy";
      image.style.cssText = "width:64px;height:64px;object-fit:cover;border-radius:8px;margin-inline-start:8px;";
      image.onerror = () => image.remove();
      parentRow.append(image);
    }

    const parentEdit = makeButton("تعديل", () => beginCategoryEdit(parent));
    const parentToggle = makeButton(parent.is_active ? "إيقاف" : "تفعيل", async () => {
      parentToggle.disabled = true;
      const { error } = await supabase.from("categories")
        .update({ is_active: !parent.is_active }).eq("id", parent.id);
      if (error) {
        alert(`تعذر تغيير حالة القسم: ${error.message}`);
        parentToggle.disabled = false;
        return;
      }
      await loadCategories();
    });
    const parentDelete = makeButton("حذف", () => deleteCategory(parent));
    parentRow.append(parentInfo, parentEdit, parentToggle, parentDelete);
    container.append(parentRow);

    const children = visible
      .filter(category => String(category.parent_id) === String(parent.id))
      .sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0) || a.name.localeCompare(b.name, "ar"));

    children.forEach(child => {
      const childRow = document.createElement("div");
      childRow.className = "item category-child-item";

      const childInfo = document.createElement("div");
      childInfo.className = "info";
      childInfo.textContent = `↳ ${child.name} — فرعي من ${parent.name} — الترتيب: ${child.sort_order ?? 0} — ${child.is_active ? "نشط" : "متوقف"}`;
      if (child.image_url) {
        const image = document.createElement("img");
        image.src = child.image_url;
        image.alt = `صورة ${child.name}`;
        image.loading = "lazy";
        image.style.cssText = "width:56px;height:56px;object-fit:cover;border-radius:8px;margin-inline-start:8px;";
        image.onerror = () => image.remove();
        childRow.append(image);
      }

      const childEdit = makeButton("تعديل", () => beginCategoryEdit(child));
      const childToggle = makeButton(child.is_active ? "إيقاف" : "تفعيل", async () => {
        childToggle.disabled = true;
        const { error } = await supabase.from("categories")
          .update({ is_active: !child.is_active }).eq("id", child.id);
        if (error) {
          alert(`تعذر تغيير حالة القسم الفرعي: ${error.message}`);
          childToggle.disabled = false;
          return;
        }
        await loadCategories();
      });
      const childDelete = makeButton("حذف", () => deleteCategory(child));
      childRow.append(childInfo, childEdit, childToggle, childDelete);
      container.append(childRow);
    });
  });

  // Keep any orphaned/legacy categories visible so they can be repaired.
  visible.filter(category => category.parent_id && !getCategoryById(category.parent_id)).forEach(category => {
    const row = document.createElement("div");
    row.className = "item";
    const info = document.createElement("div");
    info.className = "info";
    info.textContent = `⚠ ${category.name} — القسم الرئيسي غير موجود`;
    row.append(info, makeButton("تعديل", () => beginCategoryEdit(category)));
    container.append(row);
  });
}

function beginCategoryEdit(category) {
  editingCategoryId = category.id;
  $("categoryName").value = category.name;
  $("categoryOrder").value = category.sort_order ?? 0;
  $("categoryActive").checked = category.is_active !== false;
  currentCategoryImageUrl = category.image_url || "";
  if ($("categoryImageFile")) $("categoryImageFile").value = "";
  setCategoryImagePreview(currentCategoryImageUrl);
  if ($("clearCategoryImage")) $("clearCategoryImage").classList.toggle("hide", !currentCategoryImageUrl);
  setMessage("categoryImageMsg", currentCategoryImageUrl ? "الصورة الحالية محفوظة. اختر صورة جديدة لاستبدالها أو أزلها." : "لا توجد صورة حالية لهذا القسم.");
  renderCategoryParentOptions(category.parent_id || "");
  $("saveCategory").textContent = "حفظ التعديلات";
  $("cancelCategoryEdit").classList.remove("hide");
  setMessage("categoryMsg", "عدّل البيانات ثم اضغط حفظ التعديلات.");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function deleteCategory(category) {
  const children = cachedCategories.filter(item => String(item.parent_id) === String(category.id));
  if (children.length) {
    alert(`لا يمكن حذف "${category.name}" لأنه يحتوي على ${children.length} قسم فرعي. احذف الأقسام الفرعية أو انقلها أولاً.`);
    return;
  }

  const { count, error: countError } = await supabase.from("products")
    .select("id", { count: "exact", head: true })
    .eq("category", category.parent_id ? (getCategoryById(category.parent_id)?.name || "") : category.name);

  if (countError) {
    alert(`تعذر التحقق من المنتجات المرتبطة: ${countError.message}`);
    return;
  }

  const { count: subCount, error: subError } = await supabase.from("products")
    .select("id", { count: "exact", head: true })
    .eq("subcategory_id", category.id);

  if (subError) {
    alert(`تعذر التحقق من المنتجات المرتبطة بالقسم الفرعي: ${subError.message}`);
    return;
  }

  if ((subCount || 0) > 0 || (!category.parent_id && (count || 0) > 0)) {
    alert(`لا يمكن حذف "${category.name}" لأنه مرتبط بمنتجات. انقل المنتجات إلى قسم آخر أولاً، أو أوقف القسم بدلاً من حذفه.`);
    return;
  }
  if (!confirm(`هل تريد حذف قسم "${category.name}" نهائياً؟`)) return;

  const { error } = await supabase.from("categories").delete().eq("id", category.id);
  if (error) {
    alert(`تعذر حذف القسم: ${error.message}`);
    return;
  }
  if (editingCategoryId === category.id) resetCategoryForm();
  await loadCategories();
}

$("categorySearch")?.addEventListener("input", renderCategoryList);
$("categoryStatusFilter")?.addEventListener("change", renderCategoryList);

async function loadCategories() {
  const container = $("categoryList");
  if (container) container.textContent = "جارٍ تحميل الأقسام...";
  const { data, error } = await supabase.from("categories")
    .select("id,name,sort_order,is_active,parent_id,image_url")
    .order("sort_order", { ascending: true })
    .order("name", { ascending: true });

  if (error) {
    if (container) container.textContent = `تعذر تحميل الأقسام: ${error.message}`;
    setMessage("categoryMsg", error.message, true);
    console.error("ASTRO categories load error:", error);
    return false;
  }

  cachedCategories = data || [];
  renderCategoryList();
  renderCategoryOptions();
  renderCategoryParentOptions();
  return true;
}

$("categoryForm")?.addEventListener("submit", async event => {
  event.preventDefault();
  if (!currentUser) return setMessage("categoryMsg", "انتهت جلسة المدير. سجّل الدخول مجدداً.", true);

  const name = $("categoryName").value.trim();
  const sort_order = Number($("categoryOrder").value);
  const is_active = $("categoryActive").checked;
  const parent_id = $("categoryParent").value || null;

  if (!name) return setMessage("categoryMsg", "اكتب اسم القسم.", true);
  if (!Number.isInteger(sort_order)) return setMessage("categoryMsg", "ترتيب الظهور يجب أن يكون رقماً صحيحاً.", true);
  if (parent_id && !getCategoryById(parent_id)) return setMessage("categoryMsg", "القسم الرئيسي المختار غير موجود.", true);
  if (editingCategoryId !== null && parent_id && getDescendantCategoryIds(editingCategoryId).has(String(parent_id))) {
    return setMessage("categoryMsg", "لا يمكن نقل القسم إلى نفسه أو إلى أحد أقسامه الفرعية.", true);
  }

  const duplicate = cachedCategories.find(category =>
    category.name.trim().toLocaleLowerCase() === name.toLocaleLowerCase() &&
    String(category.parent_id || "") === String(parent_id || "") &&
    String(category.id) !== String(editingCategoryId)
  );
  if (duplicate) return setMessage("categoryMsg", "يوجد قسم بهذا الاسم تحت نفس القسم الرئيسي بالفعل.", true);

  const saveButton = $("saveCategory");
  saveButton.disabled = true;

  try {
    let image_url = currentCategoryImageUrl || null;
    const imageFile = $("categoryImageFile")?.files?.[0];
    if (imageFile) {
      setMessage("categoryImageMsg", "جارٍ رفع صورة القسم إلى Supabase...");
      image_url = await uploadCategoryImage(imageFile);
    } else if (editingCategoryId !== null && !currentCategoryImageUrl) {
      image_url = null;
    }

    setMessage("categoryMsg", "جارٍ حفظ القسم...");

    if (editingCategoryId !== null) {
      const oldCategory = cachedCategories.find(category => String(category.id) === String(editingCategoryId));
      if (!oldCategory) throw new Error("لم يتم العثور على القسم المطلوب تعديله.");

      const { error: categoryError } = await supabase.from("categories")
        .update({ name, sort_order, is_active, parent_id, image_url }).eq("id", editingCategoryId);
      if (categoryError) throw categoryError;

      // Keep the legacy products.category field synchronized when a root category is renamed.
      if (!oldCategory.parent_id && !parent_id && oldCategory.name !== name) {
        const { error: productsError } = await supabase.from("products")
          .update({ category: name }).eq("category", oldCategory.name);
        if (productsError) {
          const { error: rollbackError } = await supabase.from("categories")
            .update({ name: oldCategory.name, parent_id: oldCategory.parent_id }).eq("id", editingCategoryId);
          if (rollbackError) console.error("ASTRO category rename rollback failed:", rollbackError);
          throw new Error(`تعذر تحديث اسم القسم في المنتجات: ${productsError.message}`);
        }
      }
      setMessage("categoryMsg", "تم تعديل القسم بنجاح.");
    setMessage("categoryImageMsg", "تم حفظ صورة القسم بنجاح.");
    } else {
      const { error } = await supabase.from("categories")
        .insert({ name, sort_order, is_active, parent_id, image_url });
      if (error) throw error;
      setMessage("categoryMsg", "تمت إضافة القسم بنجاح.");
      setMessage("categoryImageMsg", "تم حفظ صورة القسم بنجاح.");
    }

    resetCategoryForm();
    await loadCategories();
    await loadProducts();
  } catch (error) {
    setMessage("categoryMsg", error.message || "حدث خطأ أثناء حفظ القسم.", true);
  } finally {
    saveButton.disabled = false;
  }
});

$("cancelCategoryEdit")?.addEventListener("click", resetCategoryForm);

$("category")?.addEventListener("change", () => {
  renderProductSubcategoryOptions("");
});


// ========================================
// تحميل المنتجات
// ========================================

async function loadProducts() {
  const container = $("productList");

  if (!container) return;

  container.textContent = "جارٍ تحميل المنتجات...";

  const search = $("productSearch")?.value.trim() || "";
  const status = $("productStatusFilter")?.value || "all";
  const categoryName = $("productCategoryFilter")?.value || "";
  const subcategoryId = $("productSubcategoryFilter")?.value || "";
  const bindFilters = () => {
    const searchInput = $("productSearch");
    const statusSelect = $("productStatusFilter");
    const refreshButton = $("refreshProducts");
    const categoryFilter = $("productCategoryFilter");
    const subcategoryFilter = $("productSubcategoryFilter");
    if (categoryFilter && !categoryFilter.dataset.initialized) {
      const selectedRoot = categoryFilter.value;
      categoryFilter.replaceChildren(new Option("كل الأقسام", ""));
      cachedCategories.filter(c => !c.parent_id).forEach(c => categoryFilter.add(new Option(c.name, c.name)));
      categoryFilter.value = selectedRoot;
      categoryFilter.dataset.initialized = "1";
    }
    const refreshSubcategories = () => {
      if (!subcategoryFilter) return;
      const selected = subcategoryFilter.value;
      subcategoryFilter.replaceChildren(new Option("كل الأقسام الفرعية", ""));
      const root = cachedCategories.find(c => !c.parent_id && c.name === categoryFilter?.value);
      const children = root ? cachedCategories.filter(c => String(c.parent_id) === String(root.id)) : [];
      children.forEach(c => subcategoryFilter.add(new Option(c.name, String(c.id))));
      subcategoryFilter.disabled = !root || !children.length;
      if (children.some(c => String(c.id) === selected)) subcategoryFilter.value = selected;
    };
    refreshSubcategories();
    if (categoryFilter && !categoryFilter.dataset.bound) {
      categoryFilter.dataset.bound = "1";
      categoryFilter.addEventListener("change", () => {
        if (subcategoryFilter) subcategoryFilter.value = "";
        refreshSubcategories();
        loadProducts();
      });
    }
    if (subcategoryFilter && !subcategoryFilter.dataset.bound) {
      subcategoryFilter.dataset.bound = "1";
      subcategoryFilter.addEventListener("change", loadProducts);
    }
    if (searchInput && !searchInput.dataset.bound) {
      searchInput.dataset.bound = "1";
      searchInput.addEventListener("keydown", event => {
        if (event.key === "Enter") { event.preventDefault(); loadProducts(); }
      });
    }
    if (statusSelect && !statusSelect.dataset.bound) {
      statusSelect.dataset.bound = "1";
      statusSelect.addEventListener("change", loadProducts);
    }
    if (refreshButton && !refreshButton.dataset.bound) {
      refreshButton.dataset.bound = "1";
      refreshButton.addEventListener("click", loadProducts);
    }
  };
  bindFilters();

  let productsQuery = supabase
    .from("products")
    .select("*")
    .order("created_at", { ascending: false });
  if (search) productsQuery = productsQuery.ilike("name", `%${search.replace(/[,%()]/g, " ")}%`);
  if (status === "active") productsQuery = productsQuery.eq("is_active", true);
  if (status === "inactive") productsQuery = productsQuery.eq("is_active", false);
  if (categoryName) productsQuery = productsQuery.eq("category", categoryName);
  if (subcategoryId) productsQuery = productsQuery.eq("subcategory_id", subcategoryId);
  const { data, error } = await productsQuery;

  if (error) {
    container.textContent =
      `تعذر تحميل المنتجات: ${error.message}`;
    return;
  }

  container.replaceChildren();

  if (!data?.length) {
    container.textContent = search || status !== "all" ? "لا توجد نتائج مطابقة لخيارات البحث." : "لا توجد منتجات بعد.";
    if ($("productFilterMsg")) $("productFilterMsg").textContent = "عدد النتائج: 0";
    return;
  }
  if ($("productFilterMsg")) $("productFilterMsg").textContent = `عدد النتائج: ${data.length} منتج`;

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

    const subcategoryName = getCategoryById(product.subcategory_id)?.name;
    info.textContent =
      `${product.name} — ${product.category || "بدون قسم"}${subcategoryName ? ` / ${subcategoryName}` : ""} — ${product.price} د.ل — المخزون: ${product.stock} — نقاط المكافآت: ${Number(product.reward_points ?? 0)} لكل قطعة — الألوان: ${colorsText || "غير محددة"} — ${product.is_active ? "ظاهر" : "مخفي"}`;

    const edit = makeButton("تعديل", () => {
      resetForm();

      $("pid").value = product.id;
      $("name").value = product.name || "";
      renderCategoryOptions(product.category || "", product.subcategory_id || "");
      $("category").value = product.category || "";
      renderProductSubcategoryOptions(product.subcategory_id || "");
      $("price").value = product.price ?? 0;
      $("stock").value = product.stock ?? 0;
      if ($("rewardPoints")) $("rewardPoints").value = String(product.reward_points ?? 0);
      if ($("rewardEnabled")) $("rewardEnabled").checked = Number(product.reward_points ?? 0) > 0;
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
// تحميل الطلبات بالتفاصيل الكاملة وإدارة حالتها
// ========================================

const ORDER_STATUSES = [
  "جديد",
  "قيد التجهيز",
  "جاهز للاستلام",
  "خرج للتوصيل",
  "تم التسليم",
  "ملغي"
];

function addOrderField(parent, label, value) {
  const line = document.createElement("p");
  line.style.cssText = "margin:10px 0;line-height:1.8;";
  const strong = document.createElement("strong");
  strong.textContent = `${label}: `;
  line.append(strong, document.createTextNode(value || "غير محدد"));
  parent.append(line);
  return line;
}

async function updateOrderStatus(orderId, newStatus, button, message) {
  if (!currentUser) {
    message.textContent = "انتهت جلسة المدير. سجّل الدخول مجدداً.";
    return;
  }

  button.disabled = true;
  message.textContent = "جارٍ حفظ حالة الطلب...";

  try {
    const { error } = await supabase
      .from("orders")
      .update({ status: newStatus })
      .eq("id", orderId);

    if (error) throw error;

    message.textContent = "تم تحديث حالة الطلب بنجاح.";
    await loadOrders();

  } catch (error) {
    message.textContent = `تعذر تحديث الحالة: ${error.message || error}`;
    button.disabled = false;
  }
}

async function loadOrders() {
  const container = $("orderList");

  if (!container) return;

  container.textContent = "جارٍ تحميل الطلبات...";

  const { data: orders, error } = await supabase
    .from("orders")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(100);

  if (error) {
    container.textContent = `تعذر تحميل الطلبات: ${error.message}`;
    return;
  }

  container.replaceChildren();

  if (!orders?.length) {
    container.textContent = "لا توجد طلبات حالياً.";
    return;
  }

  const orderIds = orders.map(order => order.id);
  const { data: items, error: itemsError } = await supabase
    .from("order_items")
    .select("*")
    .in("order_id", orderIds);

  // لا نوقف عرض الطلبات إذا كان جدول تفاصيل المنتجات غير موجود.
  // تبقى بيانات الطلب وتغيير الحالة متاحين، مع إظهار تنبيه واضح.
  if (itemsError) {
    console.error("ASTRO MOBILE order_items error:", itemsError);
    const warning = document.createElement("p");
    warning.setAttribute("role", "alert");
    warning.style.cssText = "padding:10px;background:#fff3cd;color:#664d03;border-radius:8px;margin:10px 0;";
    warning.textContent = "تنبيه: تم تحميل الطلبات، لكن تفاصيل المنتجات غير متاحة حالياً لأن جدول order_items غير موجود أو غير ظاهر في قاعدة البيانات.";
    container.append(warning);
  }

  const itemsByOrder = new Map();
  (itemsError ? [] : (items || [])).forEach(item => {
    const list = itemsByOrder.get(item.order_id) || [];
    list.push(item);
    itemsByOrder.set(item.order_id, list);
  });

  // صور المنتجات محفوظة في جدول products.image_url؛ نربطها بتفاصيل الطلب
  // باستخدام product_id حتى لا نحتاج إلى تعديل تطبيق Flutter أو إعادة إرسال الطلب.
  const productIds = [...new Set(
    (itemsError ? [] : (items || []))
      .map(item => item.product_id)
      .filter(id => id !== null && id !== undefined && String(id).trim() !== "")
      .map(id => String(id))
  )];

  const productImages = new Map();
  if (productIds.length) {
    const { data: products, error: productsError } = await supabase
      .from("products")
      .select("id,image_url")
      .in("id", productIds);

    if (productsError) {
      console.warn("ASTRO MOBILE product images lookup error:", productsError);
    } else {
      (products || []).forEach(product => {
        if (product.image_url) {
          productImages.set(String(product.id), product.image_url);
        }
      });
    }
  }

  for (const order of orders) {
    const card = document.createElement("article");
    card.className = "item";
    card.style.cssText = "display:block;background:#fff;color:#172033;border:1px solid #ddd;border-radius:12px;padding:16px;margin:14px 0;";

    const heading = document.createElement("h3");
    heading.textContent = `طلب رقم ${order.order_number || String(order.id).slice(0, 8)}`;
    heading.style.cssText = "margin:0 0 14px;font-size:18px;";
    card.append(heading);

        addOrderField(card, "العميل", order.customer_name || order.name || "غير محدد");
    addOrderField(card, "الهاتف", order.customer_phone || order.phone || "غير محدد");
    addOrderField(card, "العنوان", order.customer_address || order.address || "غير محدد");
    addOrderField(card, "طريقة الاستلام", order.delivery_method === "pickup" ? "استلام من المتجر" : order.delivery_method === "delivery" ? "توصيل" : order.delivery_method);
    if (order.delivery_method === "delivery") {
      addOrderField(card, "مدينة التوصيل", order.delivery_city || "غير محددة");
      addOrderField(card, "رسوم التوصيل", `${Number(order.delivery_fee || 0).toFixed(2)} د.ل`);
      addOrderField(card, "مدة الوصول عند الطلب", order.delivery_estimate || "غير محددة");
    }
    addOrderField(card, "طريقة الدفع", order.payment_method === "cash" ? "نقداً عند الاستلام" : order.payment_method === "transfer" ? "تحويل مصرفي" : order.payment_method);

    const productTitle = document.createElement("h4");
    productTitle.textContent = "المنتجات المطلوبة:";
    productTitle.style.margin = "16px 0 8px";
    card.append(productTitle);

    const orderItems = itemsByOrder.get(order.id) || [];
    if (!orderItems.length) {
      addOrderField(card, "المنتجات", "لا توجد تفاصيل منتجات مسجلة لهذا الطلب");
    } else {
      orderItems.forEach(item => {
        const itemBox = document.createElement("div");
        itemBox.style.cssText = "border:1px solid #ddd;border-radius:9px;padding:10px;margin:8px 0;";
        const imageUrl = item.image_url || productImages.get(String(item.product_id));
        if (imageUrl) {
          const image = document.createElement("img");
          image.src = imageUrl;
          image.alt = item.product_name || "صورة المنتج";
          image.loading = "lazy";
          image.style.cssText = "display:block;width:88px;height:88px;object-fit:contain;border:1px solid #eee;border-radius:8px;margin:8px 0;background:#fff;";
          image.onerror = () => image.remove();
          itemBox.append(image);
        }
        addOrderField(itemBox, "المنتج", item.product_name);
        addOrderField(itemBox, "اللون", item.color || "غير محدد");
        addOrderField(itemBox, "الكمية", String(item.quantity ?? 1));
        addOrderField(itemBox, "سعر القطعة", `${item.unit_price ?? "—"} د.ل`);
        card.append(itemBox);
      });
    }

    const total = order.total ?? order.total_price ?? "—";
    const totalLine = addOrderField(card, "الإجمالي", `${total} د.ل`);
    totalLine.style.fontWeight = "bold";
    totalLine.style.fontSize = "17px";

    addOrderField(card, "تاريخ الطلب", order.created_at ? new Date(order.created_at).toLocaleString("ar-LY") : "غير محدد");

    if (order.receipt_path) {
      const receiptLine = document.createElement("p");
      receiptLine.style.margin = "10px 0";
      const receiptButton = document.createElement("button");
      receiptButton.type = "button";
      receiptButton.textContent = "عرض إيصال التحويل";
      receiptButton.addEventListener("click", async () => {
        receiptButton.disabled = true;
        try {
          const { data, error: receiptError } = await supabase
            .storage.from("receipts")
            .createSignedUrl(order.receipt_path, 300);
          if (receiptError) throw receiptError;
          window.open(data.signedUrl, "_blank", "noopener");
        } catch (error) {
          alert(`تعذر فتح الإيصال: ${error.message || error}`);
        } finally {
          receiptButton.disabled = false;
        }
      });
      receiptLine.append(receiptButton);
      card.append(receiptLine);
    }

    const statusTitle = document.createElement("h4");
    statusTitle.textContent = "حالة الطلب:";
    statusTitle.style.margin = "18px 0 8px";
    card.append(statusTitle);

    const statusSelect = document.createElement("select");
    statusSelect.style.cssText = "width:100%;padding:12px;border:1px solid #bbb;border-radius:8px;background:#fff;color:#172033;font-size:15px;";
    ORDER_STATUSES.forEach(status => {
      const option = document.createElement("option");
      option.value = status;
      option.textContent = status;
      statusSelect.append(option);
    });
    const currentStatus = order.status || "جديد";
    if (!ORDER_STATUSES.includes(currentStatus)) {
      const oldOption = document.createElement("option");
      oldOption.value = currentStatus;
      oldOption.textContent = currentStatus;
      statusSelect.append(oldOption);
    }
    statusSelect.value = currentStatus;

    const saveStatus = document.createElement("button");
    saveStatus.type = "button";
    saveStatus.textContent = "حفظ الحالة";
    saveStatus.style.cssText = "margin:10px 0;padding:11px 16px;border:0;border-radius:8px;background:#14233f;color:#fff;";

    const statusMessage = document.createElement("p");
    statusMessage.setAttribute("role", "status");
    statusMessage.style.margin = "6px 0";

    saveStatus.addEventListener("click", () => {
      updateOrderStatus(order.id, statusSelect.value, saveStatus, statusMessage);
    });

    card.append(statusSelect, saveStatus, statusMessage);
    container.append(card);
  }
}

// ========================================
// إدارة مدن التوصيل ورسومها ومدد الوصول
// ========================================

function resetDeliveryCityForm() {
  $("deliveryCityForm")?.reset();
  $("deliveryCityId").value = "";
  $("deliveryCityActive").checked = true;
  $("saveDeliveryCity").textContent = "حفظ المدينة";
  $("cancelDeliveryCity").classList.add("hide");
}

async function loadDeliveryCities() {
  const container = $("deliveryCityList");
  if (!container) return;
  container.textContent = "جارٍ تحميل المدن...";
  const { data, error } = await supabase
    .from("delivery_cities")
    .select("id,city_name,delivery_fee,estimated_delivery,is_active")
    .order("city_name", { ascending: true });
  if (error) {
    container.textContent = `تعذر تحميل المدن: ${error.message}. تأكد من تنفيذ ملف delivery_setup.sql.`;
    return;
  }
  container.replaceChildren();
  if (!data?.length) {
    container.textContent = "لا توجد مدن مضافة. استخدم النموذج لإضافة أول مدينة.";
    return;
  }
  data.forEach(city => {
    const card = document.createElement("article");
    card.className = "item";
    card.style.cssText = "display:block;background:#fff;color:#172033;border:1px solid #ddd;border-radius:12px;padding:14px;margin:12px 0;";
    const title = document.createElement("h3");
    title.textContent = city.city_name;
    card.append(title);
    addOrderField(card, "رسوم التوصيل", `${Number(city.delivery_fee).toFixed(2)} د.ل`);
    addOrderField(card, "مدة الوصول", city.estimated_delivery);
    addOrderField(card, "الحالة", city.is_active ? "متاحة للزبائن" : "متوقفة مؤقتاً");
    const edit = makeButton("تعديل", () => {
      $("deliveryCityId").value = String(city.id);
      $("deliveryCityName").value = city.city_name;
      $("deliveryCityFee").value = String(city.delivery_fee);
      $("deliveryCityEta").value = city.estimated_delivery;
      $("deliveryCityActive").checked = city.is_active;
      $("saveDeliveryCity").textContent = "حفظ التعديلات";
      $("cancelDeliveryCity").classList.remove("hide");
      $("deliveryCityForm").scrollIntoView({ behavior: "smooth", block: "start" });
    });
    const toggle = makeButton(city.is_active ? "تعطيل المدينة" : "تفعيل المدينة", async () => {
      const { error: updateError } = await supabase.from("delivery_cities")
        .update({ is_active: !city.is_active, updated_at: new Date().toISOString() })
        .eq("id", city.id);
      if (updateError) return setMessage("deliveryCityMsg", `تعذر تغيير الحالة: ${updateError.message}`, true);
      setMessage("deliveryCityMsg", "تم تحديث حالة المدينة.");
      await loadDeliveryCities();
    });
    const del = makeButton("حذف", async () => {
      if (!confirm(`هل تريد حذف مدينة ${city.city_name}؟`)) return;
      const { error: deleteError } = await supabase.from("delivery_cities").delete().eq("id", city.id);
      if (deleteError) return setMessage("deliveryCityMsg", `تعذر حذف المدينة: ${deleteError.message}`, true);
      setMessage("deliveryCityMsg", "تم حذف المدينة.");
      await loadDeliveryCities();
    });
    card.append(edit, toggle, del);
    container.append(card);
  });
}

$("deliveryCityForm")?.addEventListener("submit", async event => {
  event.preventDefault();
  if (!currentUser) return setMessage("deliveryCityMsg", "يرجى تسجيل الدخول مجدداً.", true);
  const id = $("deliveryCityId").value;
  const payload = {
    city_name: $("deliveryCityName").value.trim(),
    delivery_fee: Number($("deliveryCityFee").value),
    estimated_delivery: $("deliveryCityEta").value.trim(),
    is_active: $("deliveryCityActive").checked,
    updated_at: new Date().toISOString()
  };
  if (!payload.city_name || !payload.estimated_delivery || !Number.isFinite(payload.delivery_fee) || payload.delivery_fee < 0) {
    return setMessage("deliveryCityMsg", "تحقق من اسم المدينة والرسوم ومدة الوصول.", true);
  }
  const button = $("saveDeliveryCity");
  button.disabled = true;
  try {
    const query = id
      ? supabase.from("delivery_cities").update(payload).eq("id", id)
      : supabase.from("delivery_cities").insert(payload);
    const { error } = await query;
    if (error) throw error;
    setMessage("deliveryCityMsg", id ? "تم تعديل بيانات المدينة بنجاح." : "تمت إضافة المدينة بنجاح.");
    resetDeliveryCityForm();
    await loadDeliveryCities();
  } catch (error) {
    setMessage("deliveryCityMsg", `تعذر حفظ المدينة: ${error.message || error}`, true);
  } finally {
    button.disabled = false;
  }
});

$("cancelDeliveryCity")?.addEventListener("click", resetDeliveryCityForm);

// ========================================
// تحسين صور المنتجات إلى WebP على دفعات
// ========================================

function getProductsBucketPath(imageUrl) {
  try {
    const url = new URL(imageUrl);
    const marker = "/storage/v1/object/public/products/";
    const markerIndex = url.pathname.indexOf(marker);
    if (markerIndex < 0) return null;
    const path = decodeURIComponent(url.pathname.slice(markerIndex + marker.length));
    if (!path || path.startsWith("optimized/") || path.includes("..")) return null;
    return path;
  } catch {
    return null;
  }
}

async function optimizeAllProductImages() {
  const button = $("startImageOptimization");
  const status = $("imageOptimizationMsg");
  if (!currentUser) {
    setMessage("imageOptimizationMsg", "يرجى تسجيل الدخول بحساب المدير.", true);
    return;
  }
  if (!button || !status) return;

  const confirmed = confirm(
    "سيتم تحويل صور المنتجات إلى WebP وتحديث روابط المنتجات بعد نجاح كل صورة.\n\nستبقى الصور الأصلية محفوظة ولن يتم حذفها. هل تريد البدء؟"
  );
  if (!confirmed) return;

  button.disabled = true;
  let converted = 0;
  let failed = 0;

  try {
    const { data: products, error: productsError } = await supabase
      .from("products")
      .select("id,name,image_url")
      .order("id", { ascending: true });
    if (productsError) throw productsError;

    const pending = (products || [])
      .map(product => ({ ...product, sourcePath: getProductsBucketPath(product.image_url) }))
      .filter(product => product.sourcePath);

    if (!pending.length) {
      setMessage("imageOptimizationMsg", "لا توجد صور أصلية تحتاج إلى التحويل.");
      return;
    }

    setMessage(
      "imageOptimizationMsg",
      `تم العثور على ${pending.length} صورة تحتاج إلى التحسين. بدء المعالجة...`
    );

    for (let start = 0; start < pending.length; start += 4) {
      const batch = pending.slice(start, start + 4);
      const { data, error } = await supabase.functions.invoke(
        "optimize-product-image",
        { body: { paths: batch.map(item => item.sourcePath) } }
      );
      if (error) throw new Error(error.message || "تعذر تشغيل دالة تحسين الصور.");
      if (!data?.results || !Array.isArray(data.results)) {
        throw new Error("استجابة دالة تحسين الصور غير مكتملة.");
      }

      for (const result of data.results) {
        const product = batch.find(item => item.sourcePath === result.sourcePath);
        if (!product) continue;
        if (result.error || !result.publicUrl) {
          failed++;
          console.error("Image optimization failed:", product.id, result.error);
          continue;
        }

        const { error: updateError } = await supabase
          .from("products")
          .update({
            image_url: result.publicUrl,
            updated_at: new Date().toISOString()
          })
          .eq("id", product.id);

        if (updateError) {
          failed++;
          console.error("Product image URL update failed:", product.id, updateError);
        } else {
          converted++;
        }
      }

      const processed = Math.min(start + batch.length, pending.length);
      setMessage(
        "imageOptimizationMsg",
        `التقدم: ${processed} من ${pending.length} صورة — تم تحديث ${converted}، وتعذّر ${failed}.`
      );
    }

    await loadProducts();
    setMessage(
      "imageOptimizationMsg",
      `اكتملت المعالجة. تم تحويل وتحديث ${converted} صورة، وتعذّر ${failed}. الصور الأصلية محفوظة.`,
      failed > 0
    );
  } catch (error) {
    console.error("ASTRO image optimization:", error);
    setMessage(
      "imageOptimizationMsg",
      `توقفت العملية بعد تحديث ${converted} صورة. السبب: ${error.message || error}. يمكنك الضغط على البدء مجدداً؛ الصور المحسّنة لن يعاد تحويلها.`,
      true
    );
  } finally {
    button.disabled = false;
  }
}

$("startImageOptimization")?.addEventListener("click", optimizeAllProductImages);

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
