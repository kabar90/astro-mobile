
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

  for (const order of orders) {
    const card = document.createElement("article");
    card.className = "item";
    card.style.cssText = "display:block;background:#fff;color:#172033;border:1px solid #ddd;border-radius:12px;padding:16px;margin:14px 0;";

    const heading = document.createElement("h3");
    heading.textContent = `طلب رقم ${order.order_number || String(order.id).slice(0, 8)}`;
    heading.style.cssText = "margin:0 0 14px;font-size:18px;";
    card.append(heading);

    addOrderField(card, "العميل", order.customer_name);
    addOrderField(card, "الهاتف", order.phone);
    addOrderField(card, "العنوان", order.address || "غير محدد");
    addOrderField(card, "طريقة الاستلام", order.delivery_method === "pickup" ? "استلام من المتجر" : order.delivery_method === "delivery" ? "توصيل" : order.delivery_method);
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
