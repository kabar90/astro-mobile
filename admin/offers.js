
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
let products = [];
let offers = [];
let editingOfferId = null;
let bundleRows = [];
let multiProductRows = [];

const money = (value) =>
  `${Number(value || 0).toFixed(2)} د.ل`;

function message(text, error = false) {
  const el = $("offerMsg");
  if (!el) return;
  el.textContent = text;
  el.style.color = error ? "#b42318" : "#16734a";
}

function escapeText(value) {
  return String(value ?? "");
}

function makeButton(label, callback, className = "") {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = label;
  if (className) button.className = className;
  button.addEventListener("click", callback);
  return button;
}

function localDateValue(value) {
  if (!value) return "";
  const date = new Date(value);
  const offset = date.getTimezoneOffset() * 60000;
  return new Date(date.getTime() - offset)
    .toISOString()
    .slice(0, 16);
}

function selectedProduct(id) {
  return products.find(p => String(p.id) === String(id));
}

function addOption(select, value, label, disabled = false) {
  const option = document.createElement("option");
  option.value = String(value);
  option.textContent = label;
  option.disabled = disabled;
  select.append(option);
}

function productOptions(select, selectedId = "") {
  select.replaceChildren();
  addOption(select, "", "اختر المنتج");

  products.forEach(product => {
    const label =
      `${product.name} — ${money(product.price)} — المخزون: ${product.stock}`;

    addOption(
      select,
      product.id,
      product.is_active === false
        ? `${label} (متوقف)`
        : label,
      product.is_active === false
    );
  });

  select.value = selectedId ? String(selectedId) : "";
}

function setTypeFields() {
  const type = $("offerType").value;

  $("productOfferFields").classList.toggle(
    "hide",
    type !== "product"
  );

  $("categoryOfferFields").classList.toggle(
    "hide",
    type !== "category"
  );

  $("bundleOfferFields").classList.toggle(
    "hide",
    type !== "bundle"
  );

  $("multiProductOfferFields").classList.toggle(
    "hide",
    type !== "product"
  );

  $("offerProduct").required = false;
  $("offerCategory").required = type === "category";
  $("discountFields").classList.toggle(
    "hide",
    type === "bundle" || type === "product"
  );
  $("discountValue").required = type === "category";
  $("bundlePrice").required = type === "bundle";
}

function setDiscountFields() {
  const type = $("offerType").value;

  if (type === "category") {
    $("discountType").value = "percentage";
    $("discountType").disabled = true;
  } else {
    $("discountType").disabled = false;
  }

  const discountType = $("discountType").value;
  const label = $("discountValueLabel");
  const input = $("discountValue");

  let labelText = $("discountValueText");

  if (!labelText) {
    labelText = document.createElement("span");
    labelText.id = "discountValueText";

    Array.from(label.childNodes).forEach(node => {
      if (node.nodeType === Node.TEXT_NODE) {
        node.textContent = "";
      }
    });

    label.insertBefore(labelText, input);
  }

  labelText.textContent =
    discountType === "percentage"
      ? "نسبة الخصم (%)"
      : "سعر القطعة بعد الخصم بالدينار";

  input.max = discountType === "percentage" ? "100" : "";
}

function resetForm() {
  $("offerForm").reset();

  editingOfferId = null;
  bundleRows = [];
  multiProductRows = [];

  $("offerId").value = "";
  $("offerActive").checked = false;
  $("offerType").value = "product";
  $("discountType").value = "percentage";

  $("offerSave").textContent = "إنشاء العرض";
  $("offerCancel").classList.add("hide");

  productOptions($("offerProduct"));

  $("offerCategory").replaceChildren();
  addOption($("offerCategory"), "", "اختر القسم");

  const categories = [
    ...new Set(
      products
        .map(p => p.category)
        .filter(Boolean)
    )
  ].sort((a, b) => a.localeCompare(b, "ar"));

  categories.forEach(category => {
    addOption($("offerCategory"), category, category);
  });

  renderBundleRows();
  renderMultiProductRows();
  setTypeFields();
  setDiscountFields();
  message("");
}

function renderBundleRows() {
  const container = $("bundleItems");
  container.replaceChildren();

  if (!bundleRows.length) {
    const empty = document.createElement("p");
    empty.textContent = "لم تتم إضافة منتجات للباقة بعد.";
    container.append(empty);
  }

  bundleRows.forEach((row, index) => {
    const line = document.createElement("div");
    line.className = "offer-bundle-row";

    const select = document.createElement("select");
    select.required = false;
    productOptions(select, row.productId);

    select.addEventListener("change", () => {
      row.productId = select.value;
    });

    const quantity = document.createElement("input");
    quantity.type = "number";
    quantity.min = "1";
    quantity.step = "1";
    quantity.required = true;
    quantity.value = row.quantity;

    quantity.addEventListener("input", () => {
      row.quantity = quantity.value;
    });

    const remove = makeButton("إزالة", () => {
      bundleRows.splice(index, 1);
      renderBundleRows();
    });

    const productLabel = document.createElement("label");
    productLabel.textContent = "المنتج";
    productLabel.append(select);

    const quantityLabel = document.createElement("label");
    quantityLabel.textContent = "الكمية";
    quantityLabel.append(quantity);

    line.append(productLabel, quantityLabel, remove);
    container.append(line);
  });
}

function addBundleRow(productId = "", quantity = 1) {
  bundleRows.push({
    productId: productId ? String(productId) : "",
    quantity: String(quantity)
  });

  renderBundleRows();
}


function renderMultiProductRows() {
  const container = $("multiProductItems");
  if (!container) return;
  container.replaceChildren();

  if (!multiProductRows.length) {
    const empty = document.createElement("p");
    empty.textContent = "لم تتم إضافة منتجات لهذا العرض بعد.";
    container.append(empty);
  }

  multiProductRows.forEach((row, index) => {
    const line = document.createElement("div");
    line.className = "offer-bundle-row";

    const select = document.createElement("select");
    select.required = true;
    productOptions(select, row.productId);
    select.addEventListener("change", () => {
      row.productId = select.value;
      const product = selectedProduct(row.productId);
      if (product && (row.offerPrice === "" || row.offerPrice == null)) {
        row.offerPrice = String(product.price ?? "");
        price.value = row.offerPrice;
      }
    });

    const price = document.createElement("input");
    price.type = "number";
    price.min = "0.01";
    price.step = "0.01";
    price.required = false;
    price.placeholder = "سعر العرض بالدينار";
    price.value = row.offerPrice ?? "";
    price.addEventListener("input", () => { row.offerPrice = price.value; });

    const productLabel = document.createElement("label");
    productLabel.textContent = "المنتج";
    productLabel.append(select);

    const priceLabel = document.createElement("label");
    priceLabel.textContent = "سعر هذا المنتج في العرض (د.ل)";
    priceLabel.append(price);

    const remove = makeButton("إزالة", () => {
      multiProductRows.splice(index, 1);
      renderMultiProductRows();
    });

    line.append(productLabel, priceLabel, remove);
    container.append(line);
  });
}

function addMultiProductRow(productId = "", offerPrice = "") {
  multiProductRows.push({
    productId: productId ? String(productId) : "",
    offerPrice: offerPrice == null ? "" : String(offerPrice)
  });
  renderMultiProductRows();
}

function offerStatus(offer) {
  const now = Date.now();
  const start = new Date(offer.starts_at).getTime();
  const end = new Date(offer.ends_at).getTime();

  if (!offer.is_active) return "متوقف";
  if (now < start) return "لم يبدأ بعد";
  if (now >= end) return "منتهي";
  return "نشط";
}

function renderOffers() {
  const container = $("offerList");
  container.replaceChildren();

  if (!offers.length) {
    container.textContent = "لا توجد عروض مسجلة حتى الآن.";
    return;
  }

  offers.forEach(offer => {
    const card = document.createElement("article");
    card.className = "item offer-card";

    const info = document.createElement("div");
    info.className = "info";

    const title = document.createElement("h3");
    title.textContent = offer.name;

    const typeNames = {
      product: "عرض منتج",
      category: "عرض قسم",
      bundle: "باقة مجمعة",
    };

    const type = document.createElement("p");
    type.textContent = typeNames[offer.offer_type] || offer.offer_type;

    const details = document.createElement("p");

    if (offer.offer_type === "product") {
      details.textContent = "منتجات العرض — سعر مستقل لكل منتج";
    } else if (offer.offer_type === "category") {
      details.textContent = `القسم: ${offer.category_name}`;
    } else {
      details.textContent =
        `سعر الباقة: ${money(offer.bundle_price)}`;
    }

    const dates = document.createElement("p");
    dates.textContent =
      `من ${new Date(offer.starts_at).toLocaleString("ar-LY")} إلى ${new Date(offer.ends_at).toLocaleString("ar-LY")}`;

    const status = document.createElement("strong");
    status.textContent = `الحالة: ${offerStatus(offer)}`;

    info.append(title, type, details, dates, status);

    const edit = makeButton("تعديل", () => editOffer(offer));

    const toggle = makeButton(
      offer.is_active ? "إيقاف العرض" : "تفعيل العرض",
      () => toggleOffer(offer, toggle)
    );

    card.append(info, edit, toggle);
    container.append(card);
  });
}

async function loadProducts() {
  const { data, error } = await supabase
    .from("products")
    .select("id,name,category,price,stock,is_active")
    .order("name");

  if (error) throw error;

  products = data || [];
}

async function loadOffers() {
  const container = $("offerList");
  container.textContent = "جارٍ تحميل العروض...";

  const { data, error } = await supabase
    .from("offers")
    .select("*")
    .order("created_at", { ascending: false });

  if (error) {
    container.textContent =
      `تعذر تحميل العروض: ${error.message}`;
    return;
  }

  offers = data || [];
  renderOffers();
}

async function loadOfferItems(offerId) {
  const { data, error } = await supabase
    .from("offer_items")
    .select("product_id,quantity,offer_price")
    .eq("offer_id", offerId);

  if (error) throw error;
  return data || [];
}

async function editOffer(offer) {
  try {
    editingOfferId = offer.id;

    $("offerId").value = offer.id;
    $("offerName").value = offer.name || "";
    $("offerDescription").value = offer.description || "";

    $("offerType").value = offer.offer_type;

    // تحويل قيمة قاعدة البيانات إلى قيمة قائمة الاختيار في HTML
    $("discountType").value =
      offer.discount_type === "fixed_price"
        ? "fixed"
        : "percentage";

    $("discountValue").value =
      offer.discount_value ?? "";

    $("bundlePrice").value =
      offer.bundle_price ?? "";

    $("offerStart").value =
      localDateValue(offer.starts_at);

    $("offerEnd").value =
      localDateValue(offer.ends_at);

    $("offerActive").checked =
      offer.is_active === true;

    productOptions(
      $("offerProduct"),
      offer.product_id || ""
    );

    $("offerCategory").value =
      offer.category_name || "";

    bundleRows = [];
    multiProductRows = [];

    if (offer.offer_type === "bundle") {
      const items = await loadOfferItems(offer.id);

      bundleRows = items.map(item => ({
        productId: String(item.product_id),
        quantity: String(item.quantity)
      }));
    }

    if (offer.offer_type === "product") {
      const items = await loadOfferItems(offer.id);
      if (items.length) {
        multiProductRows = items.map(item => ({
          productId: String(item.product_id),
          offerPrice: item.offer_price == null ? "" : String(item.offer_price)
        }));
      } else if (offer.product_id) {
        const product = selectedProduct(offer.product_id);
        let oldPrice = Number(product?.price || 0);
        if (offer.discount_type === "fixed_price") oldPrice = Number(offer.discount_value);
        else if (offer.discount_type === "percentage") oldPrice *= (100 - Number(offer.discount_value)) / 100;
        multiProductRows = [{ productId: String(offer.product_id), offerPrice: oldPrice.toFixed(2) }];
      }
    }

    renderBundleRows();
    renderMultiProductRows();
    setTypeFields();
    setDiscountFields();

    $("offerSave").textContent = "حفظ التعديلات";
    $("offerCancel").classList.remove("hide");

    $("offerForm").classList.remove("hide");
    $("offerForm").scrollIntoView({
      behavior: "smooth",
      block: "start"
    });

    message("عدّل بيانات العرض ثم اضغط حفظ التعديلات.");

  } catch (error) {
    message(`تعذر فتح العرض: ${error.message}`, true);
  }
}

function validateForm() {
  const name = $("offerName").value.trim();
  const type = $("offerType").value;

  if (!name) throw new Error("اكتب اسم العرض.");

  const start = new Date($("offerStart").value);
  const end = new Date($("offerEnd").value);

  if (
    !Number.isFinite(start.getTime()) ||
    !Number.isFinite(end.getTime()) ||
    end <= start
  ) {
    throw new Error("تحقق من تاريخ بداية ونهاية العرض.");
  }

  if (type === "product") {
    // Ignore a completely empty extra row; validate only rows the admin started filling.
    multiProductRows = multiProductRows.filter(row =>
      String(row.productId || "").trim() !== "" || String(row.offerPrice || "").trim() !== ""
    );
    if (multiProductRows.length < 1) throw new Error("أضف منتجاً واحداً على الأقل إلى العرض.");
    const used = new Set();
    for (const row of multiProductRows) {
      if (!row.productId) throw new Error("اختر المنتج في كل سطر بدأت بإضافته، أو احذف السطر الفارغ.");
      if (String(row.offerPrice || "").trim() === "") throw new Error("أدخل سعر العرض لكل منتج.");
      const product = selectedProduct(row.productId);
      const price = Number(row.offerPrice);
      if (!product || product.is_active === false) throw new Error("اختر منتجاً نشطاً لكل سطر.");
      if (!Number.isFinite(price) || price <= 0 || price >= Number(product.price)) throw new Error("سعر العرض يجب أن يكون أكبر من صفر وأقل من السعر الأصلي.");
      if (used.has(String(row.productId))) throw new Error("لا تكرر المنتج نفسه في العرض.");
      used.add(String(row.productId));
    }
  }

  if (type === "category") {
    if (!$("offerCategory").value) {
      throw new Error("اختر القسم المطلوب.");
    }

    const value = Number($("discountValue").value);

    if (!Number.isFinite(value) || value <= 0 || value > 100) {
      throw new Error("نسبة خصم القسم يجب أن تكون بين 1 و100.");
    }
  }

  if (type === "product") {
    if (multiProductRows.length < 1) throw new Error("أضف منتجاً واحداً على الأقل إلى العرض.");
    const used = new Set();
    for (const row of multiProductRows) {
      const product = selectedProduct(row.productId);
      const price = Number(row.offerPrice);
      if (!product || product.is_active === false) throw new Error("اختر منتجاً نشطاً لكل سطر.");
      if (!Number.isFinite(price) || price <= 0) throw new Error("أدخل سعر عرض صحيحاً وأكبر من صفر لكل منتج.");
      if (used.has(String(row.productId))) throw new Error("لا تكرر المنتج نفسه في العرض.");
      used.add(String(row.productId));
    }
  }

  if (type === "bundle") {
    const price = Number($("bundlePrice").value);

    if (!Number.isFinite(price) || price < 0) {
      throw new Error("أدخل سعر الباقة بصورة صحيحة.");
    }

    if (bundleRows.length < 2) {
      throw new Error("الباقة يجب أن تحتوي على منتجين على الأقل.");
    }

    const used = new Set();

    for (const row of bundleRows) {
      const product = selectedProduct(row.productId);
      const quantity = Number(row.quantity);

      if (!product || product.is_active === false) {
        throw new Error("اختر منتجات نشطة لجميع مكونات الباقة.");
      }

      if (!Number.isInteger(quantity) || quantity < 1) {
        throw new Error("كمية كل منتج يجب أن تكون عدداً صحيحاً موجباً.");
      }

      if (used.has(String(row.productId))) {
        throw new Error("لا تكرر المنتج نفسه في الباقة؛ اجمع كميته في سطر واحد.");
      }

      used.add(String(row.productId));
    }
  }
}

function buildPayload() {
  const type = $("offerType").value;
  const selectedDiscountType = $("discountType").value;

  // قاعدة البيانات تقبل percentage أو fixed_price
  const databaseDiscountType =
    selectedDiscountType === "fixed"
      ? "fixed_price"
      : "percentage";

  const payload = {
    name: $("offerName").value.trim(),
    description: $("offerDescription").value.trim() || null,
    offer_type: type,

    product_id: null,

    category_name:
      type === "category"
        ? $("offerCategory").value
        : null,

    discount_type:
      type === "bundle" || type === "product"
        ? null
        : databaseDiscountType,

    discount_value:
      type === "bundle" || type === "product"
        ? null
        : Number($("discountValue").value),

    bundle_price:
      type === "bundle"
        ? Number($("bundlePrice").value)
        : null,

    starts_at: new Date(
      $("offerStart").value
    ).toISOString(),

    ends_at: new Date(
      $("offerEnd").value
    ).toISOString(),

    is_active: $("offerActive").checked,
    updated_at: new Date().toISOString()
  };

  return payload;
}

async function saveOffer(event) {
  event.preventDefault();

  if (!currentUser) {
    return message("انتهت جلسة المدير. سجّل الدخول مجدداً.", true);
  }

  const button = $("offerSave");
  button.disabled = true;

  try {
    validateForm();

    const payload = buildPayload();

    message("جارٍ حفظ العرض...");

    let offerId = editingOfferId;

    if (editingOfferId) {
      const { error } = await supabase
        .from("offers")
        .update(payload)
        .eq("id", editingOfferId);

      if (error) throw error;

    } else {
      const { data, error } = await supabase
        .from("offers")
        .insert(payload)
        .select("id")
        .single();

      if (error) throw error;
      offerId = data.id;
    }

    if (payload.offer_type === "bundle" || payload.offer_type === "product") {
      const { error: deleteError } = await supabase
        .from("offer_items")
        .delete()
        .eq("offer_id", offerId);

      if (deleteError) {
        throw new Error(
          `تم حفظ بيانات العرض، لكن تعذر تحديث مكوناته: ${deleteError.message}`
        );
      }

      const rows = payload.offer_type === "bundle"
        ? bundleRows.map(row => ({
            offer_id: offerId,
            product_id: Number(row.productId),
            quantity: Number(row.quantity)
          }))
        : multiProductRows.map(row => ({
            offer_id: offerId,
            product_id: Number(row.productId),
            quantity: 1,
            offer_price: Number(row.offerPrice)
          }));

      const { error: insertError } = await supabase
        .from("offer_items")
        .insert(rows);

      if (insertError) {
        throw new Error(
          `تعذر حفظ منتجات الباقة: ${insertError.message}`
        );
      }

    } else {
      const { error: deleteError } = await supabase
        .from("offer_items")
        .delete()
        .eq("offer_id", offerId);

      if (deleteError) throw deleteError;
    }

    message(
      editingOfferId
        ? "تم تحديث العرض ومكوناته بنجاح."
        : "تم إنشاء العرض بنجاح."
    );

    resetForm();
    await loadOffers();

  } catch (error) {
    console.error("ASTRO offers save error:", error);
    message(`تعذر حفظ العرض: ${error.message || error}`, true);

  } finally {
    button.disabled = false;
  }
}

async function toggleOffer(offer, button) {
  if (!currentUser) {
    return message("انتهت جلسة المدير. سجّل الدخول مجدداً.", true);
  }

  const next = !offer.is_active;

  if (
    next &&
    new Date(offer.ends_at).getTime() <= Date.now()
  ) {
    return message(
      "لا يمكن تفعيل عرض انتهى تاريخه. عدّل تاريخ النهاية أولاً.",
      true
    );
  }

  if (!confirm(
    next
      ? `هل تريد تفعيل العرض "${offer.name}"؟`
      : `هل تريد إيقاف العرض "${offer.name}"؟`
  )) return;

  button.disabled = true;

  try {
    const { error } = await supabase
      .from("offers")
      .update({
        is_active: next,
        updated_at: new Date().toISOString()
      })
      .eq("id", offer.id);

    if (error) throw error;

    message(next ? "تم تفعيل العرض." : "تم إيقاف العرض.");
    await loadOffers();

  } catch (error) {
    message(`تعذر تغيير حالة العرض: ${error.message}`, true);
    button.disabled = false;
  }
}

async function initializeOffers() {
  const { data, error } = await supabase.auth.getSession();

  if (error) {
    message(`تعذر التحقق من الجلسة: ${error.message}`, true);
    return;
  }

  currentUser = data.session?.user || null;

  if (
    !currentUser ||
    (currentUser.email || "").toLowerCase() !==
      ADMIN_EMAIL.toLowerCase()
  ) {
    message("يجب تسجيل الدخول بحساب المدير لفتح إدارة العروض.", true);
    return;
  }

  try {
    await loadProducts();
    resetForm();
    await loadOffers();
  } catch (error) {
    message(`تعذر تحميل بيانات العروض: ${error.message}`, true);
  }
}

$("offerForm")?.addEventListener("submit", saveOffer);

$("offerAdd")?.addEventListener("click", () => {
  resetForm();
  $("offerForm").classList.remove("hide");
  $("offerForm").scrollIntoView({
    behavior: "smooth",
    block: "start"
  });
});

$("offerCancel")?.addEventListener("click", () => {
  resetForm();
  $("offerForm").classList.add("hide");
});

$("offerType")?.addEventListener("change", () => {
  setTypeFields();
  setDiscountFields();
});

$("discountType")?.addEventListener("change", setDiscountFields);

$("addBundleItem")?.addEventListener("click", () => {
  addBundleRow();
});

$("addMultiProductItem")?.addEventListener("click", () => {
  addMultiProductRow();
});

$("refreshOffers")?.addEventListener("click", loadOffers);

// التنقل بين العروض وباقي أقسام لوحة الإدارة
document.querySelectorAll("nav button").forEach(button => {
  button.addEventListener("click", () => {
    const section = $("offers");

    if (section) {
      section.classList.toggle(
        "hide",
        button.dataset.view !== "offers"
      );
    }

    if (button.dataset.view === "offers") {
      loadOffers();
    }
  });
});

supabase.auth.onAuthStateChange((_event, session) => {
  currentUser = session?.user || null;

  if (
    currentUser &&
    currentUser.email?.toLowerCase() === ADMIN_EMAIL.toLowerCase()
  ) {
    loadProducts()
      .then(loadOffers)
      .catch(error => message(error.message, true));
  } else {
    currentUser = null;
  }
});

initializeOffers();
