(() => {
  const supabase = window.supabaseClient || window.sb;
  const nav = document.querySelector("#dash nav");
  const dash = document.getElementById("dash");
  if (!supabase || !nav || !dash || document.getElementById("passwordResetView")) return;

  const button = document.createElement("button");
  button.type = "button";
  button.dataset.view = "passwordReset";
  button.textContent = "استرجاع كلمة المرور";
  nav.append(button);

  const panel = document.createElement("section");
  panel.id = "passwordResetView";
  panel.className = "card hide";
  panel.innerHTML = `
    <h2>إعادة تعيين كلمة مرور عميل</h2>
    <p>تحقق أولاً من هوية العميل عبر واتساب الرسمي للمتجر قبل تغيير كلمة المرور.</p>
    <label>رقم هاتف العميل
      <input id="astroResetPhone" type="tel" inputmode="tel" placeholder="0944005010 أو +218944005010" autocomplete="off">
    </label>
    <label>كلمة المرور الجديدة (8 أحرف على الأقل)
      <input id="astroResetPassword" type="password" minlength="8" maxlength="72" autocomplete="new-password">
    </label>
    <button id="astroResetSubmit" type="button">تعيين كلمة المرور</button>
    <p id="astroResetMessage" role="status"></p>
  `;
  dash.append(panel);

  const views = ["products", "categories", "orders", "delivery", "bank", "notifications", "history"];
  button.addEventListener("click", () => {
    views.forEach(id => document.getElementById(id)?.classList.add("hide"));
    panel.classList.remove("hide");
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  document.getElementById("astroResetSubmit").addEventListener("click", async () => {
    const phone = document.getElementById("astroResetPhone").value.trim();
    const passwordInput = document.getElementById("astroResetPassword");
    const new_password = passwordInput.value;
    const message = document.getElementById("astroResetMessage");
    const submit = document.getElementById("astroResetSubmit");

    if (!phone) {
      message.textContent = "أدخل رقم هاتف العميل.";
      message.style.color = "#b42318";
      return;
    }
    if (new_password.length < 8 || new_password.length > 72) {
      message.textContent = "كلمة المرور يجب أن تكون من 8 إلى 72 حرفاً.";
      message.style.color = "#b42318";
      return;
    }
    if (!confirm("هل تحققت من هوية صاحب الحساب عبر واتساب؟ سيتم تغيير كلمة مروره فوراً.")) return;

    submit.disabled = true;
    message.textContent = "جارٍ التحقق وتغيير كلمة المرور...";
    message.style.color = "#16734a";
    try {
      const { data, error } = await supabase.functions.invoke("admin-reset-password", {
        body: { phone, new_password }
      });
      if (error) throw error;
      if (data?.error) throw new Error(data.error);
      message.textContent = data?.message || "تم تغيير كلمة المرور بنجاح.";
      message.style.color = "#16734a";
      passwordInput.value = "";
    } catch (error) {
      message.textContent = error?.message || "تعذر تغيير كلمة المرور.";
      message.style.color = "#b42318";
    } finally {
      submit.disabled = false;
    }
  });
})();

