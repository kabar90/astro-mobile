
import { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm";

import {
  SUPABASE_URL,
  SUPABASE_PUBLISHABLE_KEY,
  ADMIN_EMAIL
} from "./supabase-config.js";

// الاتصال بقاعدة بيانات ASTRO MOBILE
const supabase = createClient(
  SUPABASE_URL,
  SUPABASE_PUBLISHABLE_KEY
);

const $ = (id) => document.getElementById(id);

let loading = false;

// =====================================
// تنسيق لوحة الإشعارات
// =====================================

function addNotificationStyles() {
  if ($("astro-notification-styles")) return;

  const style = document.createElement("style");
  style.id = "astro-notification-styles";

  style.textContent = `
    #notificationHistory {
      overflow-x: auto;
      background: white;
      border-radius: 10px;
      padding: 10px;
    }

    #notificationHistory table {
      width: 100%;
      min-width: 550px;
      border-collapse: collapse;
    }

    #notificationHistory th,
    #notificationHistory td {
      padding: 12px 8px;
      text-align: right;
      border-bottom: 1px solid #eee;
      font-size: 13px;
    }

    #notificationHistory th {
      color: #64748b;
    }

    .astro-sent {
      color: #16a34a;
      font-weight: bold;
    }

    .astro-failed {
      color: #dc2626;
      font-weight: bold;
    }

    #refreshNotifications:disabled {
      opacity: .6;
      cursor: wait;
    }
  `;

  document.head.appendChild(style);
}

// =====================================
// عرض الرسائل
// =====================================

function showMessage(message, error = false) {
  const element = $("notificationMsg");

  if (!element) return;

  element.textContent = message;
  element.style.color = error ? "#dc2626" : "#64748b";
}

// =====================================
// التحقق من حساب المدير
// =====================================

async function checkAdmin() {
  const { data, error } = await supabase.auth.getSession();

  if (error) throw error;

  const user = data.session?.user;

  if (
    !user ||
    (user.email || "").toLowerCase() !== ADMIN_EMAIL.toLowerCase()
  ) {
    throw new Error("يرجى تسجيل الدخول بحساب المدير.");
  }

  return true;
}

// =====================================
// جلب إحصائيات الأجهزة
// =====================================

async function loadDeviceCount() {
  const { count, error } = await supabase
    .from("astro_device_tokens")
    .select("token", {
      count: "exact",
      head: true
    })
    .not("token", "is", null);

  if (error) throw error;

  $("notifyTotal").textContent = count ?? 0;
}

// =====================================
// تحميل سجل الإشعارات والإحصائيات
// =====================================

async function loadNotifications() {
  if (loading) return;

  loading = true;

  const refreshButton = $("refreshNotifications");

  if (refreshButton) {
    refreshButton.disabled = true;
    refreshButton.textContent = "جارٍ التحديث...";
  }

  showMessage("جارٍ تحميل بيانات الإشعارات...");

  try {
    await checkAdmin();

    // إجمالي الأجهزة
    await loadDeviceCount();

    // سجل عمليات الإرسال
    const { data, error } = await supabase
      .from("astro_notification_history")
      .select("*")
      .order("created_at", { ascending: false })
      .limit(100);

    if (error) throw error;

    const history = data || [];

    // حساب الإرسال الناجح والفاشل
    const sent = history.reduce(
      (sum, item) => sum + (Number(item.sent_count) || 0),
      0
    );

    const failed = history.reduce(
      (sum, item) => sum + (Number(item.failed_count) || 0),
      0
    );

    $("notifySent").textContent = sent;
    $("notifyFailed").textContent = failed;

    // عرض سجل الإشعارات
    const container = $("notificationHistory");

    if (!container) {
      throw new Error("لم يتم العثور على جدول سجل الإشعارات.");
    }

    if (!history.length) {
      container.textContent = "لا توجد إشعارات مسجلة حتى الآن.";
    } else {
      const table = document.createElement("table");

      const thead = document.createElement("thead");
      const headerRow = document.createElement("tr");

      [
        "العنوان",
        "الأجهزة",
        "تم الإرسال",
        "فشل",
        "الحالة",
        "التاريخ"
      ].forEach(label => {
        const th = document.createElement("th");
        th.textContent = label;
        headerRow.appendChild(th);
      });

      thead.appendChild(headerRow);
      table.appendChild(thead);

      const tbody = document.createElement("tbody");

      history.forEach(item => {
        const row = document.createElement("tr");

        const status = item.delivery_status || "queued";

        const statusText =
          status === "sent" ? "تم الإرسال" :
          status === "failed" ? "فشل الإرسال" :
          "قيد الانتظار";

        const values = [
          item.title || "-",
          Number(item.total_devices) || 0,
          Number(item.sent_count) || 0,
          Number(item.failed_count) || 0,
          statusText,
          item.created_at
            ? new Date(item.created_at).toLocaleString("ar-LY")
            : "-"
        ];

        values.forEach((value, index) => {
          const td = document.createElement("td");
          td.textContent = String(value);

          if (index === 4) {
            td.className =
              status === "sent" ? "astro-sent" :
              status === "failed" ? "astro-failed" : "";
          }

          row.appendChild(td);
        });

        tbody.appendChild(row);
      });

      table.appendChild(tbody);

      container.replaceChildren(table);
    }

    showMessage("تم تحديث الإحصائيات وسجل الإشعارات بنجاح.");

  } catch (error) {
    console.error("ASTRO notifications:", error);

    showMessage(
      `تعذر تحديث البيانات: ${error.message || error}`,
      true
    );

    if ($("notificationHistory")) {
      $("notificationHistory").textContent =
        error.message || "حدث خطأ أثناء تحميل البيانات.";
    }

  } finally {
    loading = false;

    if (refreshButton) {
      refreshButton.disabled = false;
      refreshButton.textContent = "تحديث البيانات";
    }
  }
}

// =====================================
// زر تحديث البيانات
// =====================================

function initializeNotifications() {
  addNotificationStyles();

  const button = $("refreshNotifications");

  if (button) {
    button.removeEventListener("click", loadNotifications);
    button.addEventListener("click", loadNotifications);
  }

  loadNotifications();
}

// =====================================
// تشغيل النظام
// =====================================

if (document.readyState === "loading") {
  document.addEventListener(
    "DOMContentLoaded",
    initializeNotifications
  );
} else {
  initializeNotifications();
}

window.ASTRONotifications = {
  refresh: loadNotifications
};
