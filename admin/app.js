
import { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm";
import {
  SUPABASE_URL,
  SUPABASE_PUBLISHABLE_KEY,
  ADMIN_EMAIL
} from "./supabase-config.js";

const supabase = createClient(
  SUPABASE_URL,
  SUPABASE_PUBLISHABLE_KEY
);

const $ = (id) => document.getElementById(id);

let currentUser = null;
let currentImageUrl = "";

const setMessage = (id, message, error = false) => {
  const el = $(id);
  if (!el) return;
  el.textContent = message;
  el.style.color = error ? "#b42318" : "#16734a";
};

async function showSession(session) {
  const user = session?.user;

  if (
    user &&
    (user.email || "").toLowerCase() === ADMIN_EMAIL.toLowerCase()
  ) {
    currentUser = user;

    $("login").classList.add("hide");
    $("dash").classList.remove("hide");
    $("logout").classList.remove("hide");

    await Promise.all([
      loadProducts(),
      loadOrders(),
      loadBankSettings()
    ]);
  } else {
    currentUser = null;

    if (user) await supabase.auth.signOut();

    $("login").classList.remove("hide");
    $("dash").classList.add("hide");
    $("logout").classList.add("hide");
  }
}

// تسجيل الدخول
$("loginBtn").addEventListener("click", async () => {
  const email = $("email").value.trim();
  const password = $("password").value;

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
      throw new Error("هذا الحساب غير مصرح له بإدارة المتجر.");
    }

    setMessage("loginMsg", "تم تسجيل الدخول.");
    await showSession(data.session);

  } catch (e) {
    setMessage(
      "loginMsg",
      e.message || "تعذر تسجيل الدخول. تحقق من البيانات.",
      true
    );
  } finally {
    $("loginBtn").disabled = false;
  }
});

// تسجيل الخروج
$("logout").addEventListener("click", async () => {
  await supabase.auth.signOut();
  await showSession(null);
});

supabase.auth.onAuthStateChange((_event, session) => {
  showSession(session);
});

// التنقل بين المنتجات والطلبات والحساب المصرفي
document.querySelectorAll("nav button").forEach(button => {
  button.addEventListener("click", () => {
    ["products", "orders", "bank"].forEach(view => {
      $(view).classList.toggle(
        "hide",
        view !== button.dataset.view
      );
    });
  });
});

// إعادة ضبط نموذج المنتج
function resetForm() {
  $("form").reset();

  $("pid").value = "";
  $("colors").value = "";

  currentImageUrl = "";
  $("imageUrl").value = "";

  $("preview").removeAttribute("src");
  $("preview").classList.add("hide");

  $("active").checked = true;

  $("uploadMsg").textContent =
    "اختر صورة من هاتفك، وسيتم رفعها إلى Supabase عند حفظ المنتج.";

  setMessage("formMsg", "");
}

// إضافة منتج
$("add").addEventListener("click", () => {
  resetForm();
  $("form").classList.remove("hide");
});

// إلغاء
$("cancel").addEventListener("click", () => {
  $("form").classList.add("hide");
});

// اختيار صورة المنتج
$("imageFile").addEventListener("change", () => {
  const file = $("imageFile").files?.[0];

  if (!file) return;

  if (!file.type.startsWith("image/")) {
    setMessage("formMsg", "اختر ملف صورة صالحاً.", true);
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

// رفع صورة المنتج
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
      "انتهت جلسة المدير. سجّل الخروج ثم الدخول مجدداً."
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

  const path = `${Date.now()}-${crypto.randomUUID()}.${ext}`;

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
        "انتهت مهلة رفع الصورة بعد 45 ثانية. جرّب صورة أصغر أو أعد المحاولة."
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
      detail = body.message || body.error || JSON.stringify(body);
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

// حفظ المنتج أو تعديله
$("form").addEventListener("submit", async (event) => {
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

  saveButton.disabled = true;

  try {
    let imageUrl =
      currentImageUrl || $("imageUrl").value.trim();

    const file = $("imageFile").files?.[0];

    if (file) {
      $("uploadMsg").textContent =
        "جارٍ رفع الصورة إلى Supabase... لا تغلق الصفحة.";

      imageUrl = await uploadProductImage(file);
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
      colors,
      image_url: imageUrl || null,
      is_active: $("active").checked,
      updated_at: new Date().toISOString()
    };

    if (
      !record.name ||
      !Number.isFinite(record.price) ||
      !Number.isFinite(record.stock)
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

    setMessage("formMsg", "تم حفظ المنتج بنجاح.");

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
    saveButton.disabled = false;
  }
});

// إنشاء الأزرار
function makeButton(label, action) {
  const b = document.createElement("button");
  b.textContent = label;
  b.addEventListener("click", action);
  return b;
}

// تحميل المنتجات
async function loadProducts() {
  const container = $("productList");

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

// تحميل بيانات التحويل المصرفي
async function loadBankSettings() {
  setMessage("bankMsg", "جارٍ تحميل بيانات الحساب...");

  const { data, error } = await supabase
    .from("bank_transfer_settings")
    .select("*")
    .eq("id", 1)
    .maybeSingle();

  if (error) {
    setMessage(
      "bankMsg",
      `تعذر تحميل بيانات الحساب: ${error.message}`,
      true
    );
    return;
  }

  const settings = data || {};

  $("bankName").value =
    settings.bank_name || "مصرف شمال أفريقيا";

  $("accountHolder").value =
    settings.account_holder || "";

  $("branchName").value =
    settings.branch_name || "";

  $("accountNumber").value =
    settings.account_number || "";

  $("iban").value =
    settings.iban || "";

  $("accountDetails").value =
    settings.account_details || "";

  setMessage(
    "bankMsg",
    data
      ? "تم تحميل بيانات الحساب."
      : "أدخل بيانات الحساب ثم اضغط حفظ."
  );
}

// حفظ بيانات التحويل المصرفي
$("bankForm").addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!currentUser) {
    return setMessage(
      "bankMsg",
      "انتهت جلسة المدير. سجّل الدخول مجدداً.",
      true
    );
  }

  const saveButton =
    $("bankForm").querySelector('button[type="submit"]');

  saveButton.disabled = true;

  try {
    const record = {
      id: 1,
      bank_name: $("bankName").value.trim(),
      account_holder: $("accountHolder").value.trim(),
      branch_name: $("branchName").value.trim(),
      account_number: $("accountNumber").value.trim(),
      iban: $("iban").value.trim(),
      account_details: $("accountDetails").value.trim(),
      updated_at: new Date().toISOString()
    };

    if (!record.bank_name || !record.account_holder) {
      throw new Error(
        "أدخل اسم المصرف واسم صاحب الحساب."
      );
    }

    const { error } = await supabase
      .from("bank_transfer_settings")
      .upsert(record, { onConflict: "id" });

    if (error) throw error;

    setMessage(
      "bankMsg",
      "تم حفظ بيانات الحساب المصرفي بنجاح."
    );

  } catch (error) {
    setMessage(
      "bankMsg",
      error.message || "تعذر حفظ بيانات الحساب.",
      true
    );
  } finally {
    saveButton.disabled = false;
  }
});

// تحميل الطلبات مع صور المنتجات وإيصالات التحويل
async function loadOrders() {
  const container = $("orderList");

  container.textContent = "جارٍ تحميل الطلبات...";

  const { data: orders, error } = await supabase
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

  if (!orders?.length) {
    container.textContent = "لا توجد طلبات حالياً.";
    return;
  }

  const productsMap = {};
  const productIds = [];

  orders.forEach(order => {
    let items = order.items;

    if (typeof items === "string") {
      try {
        items = JSON.parse(items);
      } catch {
        items = [];
      }
    }

    if (!Array.isArray(items)) items = [];

    order.parsedItems = items;

    items.forEach(item => {
      if (item.product_id != null) {
        productIds.push(String(item.product_id));
      }
    });
  });

  const uniqueIds = [...new Set(productIds)];

  if (uniqueIds.length) {
    const { data: products, error: productError } =
      await supabase
        .from("products")
        .select("id,name,image_url")
        .in("id", uniqueIds);

    if (!productError && products) {
      products.forEach(product => {
        productsMap[String(product.id)] = product;
      });
    }
  }

  for (const order of orders) {
    const card = document.createElement("div");
    card.className = "item";
    card.style.display = "block";
    card.style.padding = "15px";
    card.style.marginBottom = "15px";

    const title = document.createElement("h3");
    title.textContent = `طلب رقم ${order.id}`;
    card.append(title);

    const addText = (label, value) => {
      const p = document.createElement("p");
      p.textContent =
        `${label}: ${value || "غير محدد"}`;
      card.append(p);
    };

    addText("العميل", order.customer_name);
    addText("الهاتف", order.customer_phone);
    addText("العنوان", order.customer_address);
    addText("طريقة الاستلام", order.delivery_method);
    addText("طريقة الدفع", order.payment_method);

    const heading = document.createElement("h4");
    heading.textContent = "المنتجات المطلوبة:";
    card.append(heading);

    order.parsedItems.forEach(item => {
      const product =
        productsMap[String(item.product_id)] || {};

      const row = document.createElement("div");
      row.style.display = "flex";
      row.style.alignItems = "center";
      row.style.gap = "12px";
      row.style.padding = "10px";
      row.style.marginBottom = "8px";
      row.style.border = "1px solid #ddd";
      row.style.borderRadius = "10px";

      const imageUrl =
        product.image_url ||
        item.image_url ||
        item.imageUrl ||
        "";

      if (imageUrl) {
        const img = document.createElement("img");
        img.src = imageUrl;
        img.alt = product.name || "صورة المنتج";
        img.style.width = "85px";
        img.style.height = "85px";
        img.style.objectFit = "contain";
        img.style.borderRadius = "8px";
        row.append(img);
      }

      const details = document.createElement("div");
      details.style.flex = "1";

      const name = document.createElement("strong");
      name.textContent =
        product.name ||
        item.product_name ||
        `منتج رقم ${item.product_id || ""}`;

      const color = document.createElement("p");
      color.textContent =
        `اللون: ${item.color || "غير محدد"}`;

      const quantity = document.createElement("p");
      quantity.textContent =
        `الكمية: ${item.quantity || 1}`;

      const price = document.createElement("p");
      price.textContent =
        `سعر القطعة: ${item.unit_price ?? "—"} د.ل`;

      details.append(name, color, quantity, price);
      row.append(details);
      card.append(row);
    });

    const total = document.createElement("h3");
    total.textContent =
      `الإجمالي: ${order.total_price ?? order.total ?? "—"} د.ل`;

    card.append(total);

    addText("الحالة", order.status || "جديد");

    // عرض إيصال التحويل المصرفي
    if (
      order.payment_method === "transfer" &&
      order.receipt_path
    ) {
      const receiptTitle = document.createElement("h4");
      receiptTitle.textContent = "إيصال التحويل المصرفي";
      card.append(receiptTitle);

      const { data: receiptData, error: receiptError } =
        await supabase.storage
          .from("receipts")
          .createSignedUrl(order.receipt_path, 3600);

      if (!receiptError && receiptData?.signedUrl) {
        const receiptImage = document.createElement("img");

        receiptImage.src = receiptData.signedUrl;
        receiptImage.alt = "إيصال التحويل المصرفي";
        receiptImage.style.display = "block";
        receiptImage.style.width = "100%";
        receiptImage.style.maxWidth = "350px";
        receiptImage.style.maxHeight = "450px";
        receiptImage.style.objectFit = "contain";
        receiptImage.style.border = "1px solid #ddd";
        receiptImage.style.borderRadius = "10px";
        receiptImage.style.margin = "10px 0";
        receiptImage.style.cursor = "zoom-in";

        receiptImage.addEventListener("click", () => {
          window.open(receiptData.signedUrl, "_blank");
        });

        card.append(receiptImage);

        const openReceipt = makeButton(
          "فتح الإيصال بالحجم الكامل",
          () => window.open(receiptData.signedUrl, "_blank")
        );

        card.append(openReceipt);

      } else {
        const errorText = document.createElement("p");

        errorText.textContent =
          "تعذر عرض الإيصال. تحقق من صلاحيات مخزن receipts.";

        errorText.style.color = "#b42318";
        card.append(errorText);
      }
    }

    container.append(card);
  }
}

// استعادة جلسة المدير عند فتح الصفحة
const { data: initial } =
  await supabase.auth.getSession();

await showSession(initial.session);
        
