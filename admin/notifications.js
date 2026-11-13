
/* =====================================
   ASTRO MOBILE - NOTIFICATIONS DASHBOARD
   ===================================== */

(function () {
  "use strict";

  const getClient = () =>
    window.supabaseClient ||
    window.sb ||
    window.supabase;

  const client = getClient();

  const styles = `
    .notification-dashboard {
      direction: rtl;
      font-family: inherit;
      margin: 20px 0;
      color: #172033;
    }

    .notification-dashboard h2 {
      margin-bottom: 18px;
    }

    .notification-stats {
      display: grid;
      grid-template-columns: repeat(auto-fit,minmax(145px,1fr));
      gap: 12px;
      margin-bottom: 24px;
    }

    .notification-stat {
      background: white;
      border-radius: 12px;
      padding: 18px;
      border: 1px solid #e5e7eb;
      box-shadow: 0 2px 8px #00000008;
    }

    .notification-stat span {
      display: block;
      color: #64748b;
      font-size: 13px;
      margin-bottom: 10px;
    }

    .notification-stat strong {
      font-size: 27px;
      color: #14213d;
    }

    .notification-history {
      background: white;
      border-radius: 12px;
      padding: 16px;
      overflow-x: auto;
    }

    .notification-history table {
      width: 100%;
      border-collapse: collapse;
      min-width: 550px;
    }

    .notification-history th,
    .notification-history td {
      padding: 12px;
      text-align: right;
      border-bottom: 1px solid #eee;
      font-size: 13px;
    }

    .notification-status {
      font-weight: bold;
    }

    .notification-status.sent {
      color: #16a34a;
    }

    .notification-status.failed {
      color: #dc2626;
    }

    .notification-refresh {
      background: #14213d;
      color: white;
      border: 0;
      border-radius: 8px;
      padding: 10px 18px;
      margin-bottom: 15px;
      cursor: pointer;
    }
  `;

  function addStyles() {
    if (document.getElementById("astro-notifications-style")) return;

    const style = document.createElement("style");
    style.id = "astro-notifications-style";
    style.textContent = styles;
    document.head.appendChild(style);
  }

  function createDashboard() {
    let dashboard = document.getElementById(
      "astro-notification-dashboard"
    );

    if (dashboard) return dashboard;

    dashboard = document.createElement("section");
    dashboard.id = "astro-notification-dashboard";
    dashboard.className = "notification-dashboard";

    dashboard.innerHTML = `
      <h2>إحصائيات الإشعارات</h2>

      <div class="notification-stats">
        <div class="notification-stat">
          <span>إجمالي الأجهزة المسجلة</span>
          <strong id="astro-total-devices">0</strong>
        </div>

        <div class="notification-stat">
          <span>الإشعارات المرسلة</span>
          <strong id="astro-sent-count">0</strong>
        </div>

        <div class="notification-stat">
          <span>الإشعارات الفاشلة</span>
          <strong id="astro-failed-count">0</strong>
        </div>

        <div class="notification-stat">
          <span>عمليات الإرسال</span>
          <strong id="astro-total-requests">0</strong>
        </div>
      </div>

      <h2>سجل الإشعارات</h2>

      <button class="notification-refresh"
        id="astro-refresh-notifications">
        تحديث البيانات
      </button>

      <div class="notification-history">
        <table>
          <thead>
            <tr>
              <th>العنوان</th>
              <th>الأجهزة</th>
              <th>تم الإرسال</th>
              <th>فشل</th>
              <th>الحالة</th>
              <th>التاريخ</th>
            </tr>
          </thead>

          <tbody id="astro-notification-rows">
            <tr><td colspan="6">جاري تحميل البيانات...</td></tr>
          </tbody>
        </table>
      </div>
    `;

    const main =
      document.querySelector("main") ||
      document.querySelector(".container") ||
      document.body;

    main.appendChild(dashboard);

    return dashboard;
  }

  async function loadNotifications() {
    if (!client || typeof client.from !== "function") {
      console.error("ASTRO MOBILE: Supabase client not found");
      return;
    }

    const totalElement = document.getElementById(
      "astro-total-devices"
    );

    if (!totalElement) return;

    totalElement.textContent = "...";

    try {
      const deviceResult = await client
        .from("astro_device_tokens")
        .select("*", { count: "exact", head: true })
        .not("token", "is", null);

      if (deviceResult.error) throw deviceResult.error;

      document.getElementById(
        "astro-total-devices"
      ).textContent = deviceResult.count ?? 0;

      const historyResult = await client
        .from("astro_notification_history")
        .select("*")
        .order("created_at", { ascending: false })
        .limit(30);

      if (historyResult.error) throw historyResult.error;

      const history = historyResult.data || [];

      const sent = history.reduce(
        (sum, item) => sum + (Number(item.sent_count) || 0),
        0
      );

      const failed = history.reduce(
        (sum, item) => sum + (Number(item.failed_count) || 0),
        0
      );

      document.getElementById(
        "astro-sent-count"
      ).textContent = sent;

      document.getElementById(
        "astro-failed-count"
      ).textContent = failed;

      document.getElementById(
        "astro-total-requests"
      ).textContent = history.length;

      const rows = document.getElementById(
        "astro-notification-rows"
      );

      if (!history.length) {
        rows.innerHTML =
          '<tr><td colspan="6">لا توجد إشعارات حتى الآن</td></tr>';
        return;
      }

      rows.innerHTML = history.map(item => {
        const status = item.delivery_status || "queued";

        const statusText =
          status === "sent" ? "تم الإرسال" :
          status === "failed" ? "فشل الإرسال" :
          "قيد الانتظار";

        const statusClass =
          status === "sent" ? "sent" :
          status === "failed" ? "failed" : "";

        const date = item.created_at
          ? new Date(item.created_at).toLocaleString("ar-LY")
          : "-";

        return `
          <tr>
            <td>${escapeHTML(item.title || "-")}</td>
            <td>${Number(item.total_devices) || 0}</td>
            <td>${Number(item.sent_count) || 0}</td>
            <td>${Number(item.failed_count) || 0}</td>
            <td>
              <span class="notification-status ${statusClass}">
                ${statusText}
              </span>
            </td>
            <td>${escapeHTML(date)}</td>
          </tr>
        `;
      }).join("");

    } catch (error) {
      console.error("ASTRO notifications error:", error);

      document.getElementById(
        "astro-notification-rows"
      ).innerHTML =
        '<tr><td colspan="6">تعذر تحميل البيانات. تحقق من صلاحيات قاعدة البيانات.</td></tr>';
    }
  }

  function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, char => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;"
    })[char]);
  }

  function initialize() {
    addStyles();
    createDashboard();

    document.getElementById(
      "astro-refresh-notifications"
    ).addEventListener("click", loadNotifications);

    loadNotifications();
  }

  window.ASTRONotifications = {
    initialize,
    refresh: loadNotifications
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize);
  } else {
    initialize();
  }

})();

