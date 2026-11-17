// ASTRO MOBILE - إدارة أقسام الصفحة الرئيسية
// يعتمد على window.sb الذي ينشئه admin/app.js
(() => {
  const SECTION_DEFS = [
    { key: 'best_selling', title: 'الأكثر مبيعاً', description: 'اختر المنتجات التي تريد إبرازها كالأكثر مبيعاً.' },
    { key: 'used', title: 'مستعمل بحالة ممتازة', description: 'اختر الأجهزة المستعملة التي تريد عرضها.' },
    { key: 'accessories', title: 'كماليات لا غنى عنها', description: 'اختر السماعات والشواحن والملحقات.' },
    { key: 'budget', title: 'خيارات تناسب ميزانيتك', description: 'اختر المنتجات المناسبة لهذا القسم ورتبها.' },
    { key: 'astro_picks', title: 'اختيارات ASTRO', description: 'منتجات تختارها بنفسك لتظهر في هذا القسم.' },
  ];
  const $ = (id) => document.getElementById(id);
  const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function init() {
    const nav = document.querySelector('#dash nav');
    const dash = $('dash');
    if (!nav || !dash || $('homeSectionsView')) return;

    const navButton = document.createElement('button');
    navButton.type = 'button';
    navButton.textContent = 'أقسام الصفحة الرئيسية';
    navButton.dataset.view = 'homeSectionsView';
    nav.append(navButton);

    const panel = document.createElement('section');
    panel.id = 'homeSectionsView';
    panel.className = 'card hide';
    panel.innerHTML = `
      <h2>إدارة أقسام الصفحة الرئيسية</h2>
      <p>اختر المنتجات التي تريد ظهورها في كل قسم، وحدد ترتيبها. يمكنك وضع المنتج في أكثر من قسم دون إنشاء نسخة أخرى منه.</p>
      <p id="homeSectionsStatus" role="status">جارٍ تحميل البيانات...</p>
      <div id="homeSectionsForms"></div>`;
    dash.append(panel);

    navButton.addEventListener('click', () => {
      dash.querySelectorAll(':scope > .card').forEach(card => card.classList.add('hide'));
      panel.classList.remove('hide');
      nav.querySelectorAll('button').forEach(b => b.classList.remove('active'));
      navButton.classList.add('active');
      load();
    });

    // Keep the existing dashboard views working; the custom view is additive only.
    const style = document.createElement('style');
    style.textContent = `#homeSectionsView .hs-box{border:1px solid #d7e5f2;border-radius:14px;padding:15px;margin:14px 0;background:#f8fbff}#homeSectionsView .hs-grid{display:grid;grid-template-columns:1fr;gap:10px}#homeSectionsView select[multiple]{min-height:190px}#homeSectionsView .hs-meta{color:#66809a;font-size:13px}#homeSectionsView .hs-actions{display:flex;gap:8px;flex-wrap:wrap;align-items:center}#homeSectionsView .hs-toggle{display:flex;align-items:center;gap:8px}#homeSectionsView .hs-toggle input{width:auto}#homeSectionsView button{margin:4px 0}`;
    document.head.append(style);
  }

  async function load() {
    const status = $('homeSectionsStatus');
    const host = $('homeSectionsForms');
    const sb = window.sb || window.supabaseClient;
    if (!sb) { status.textContent = 'تعذر الاتصال بقاعدة البيانات. افتح لوحة الإدارة بعد تسجيل الدخول.'; return; }
    status.textContent = 'جارٍ تحميل المنتجات وإعدادات الأقسام...';
    const [{ data: products, error: productsError }, { data: saved, error: sectionsError }] = await Promise.all([
      sb.from('products').select('id,name,category,price,image_url,is_active').eq('is_active', true).order('name'),
      sb.from('home_page_sections').select('*').order('sort_order')
    ]);
    if (productsError) { status.textContent = `تعذر تحميل المنتجات: ${productsError.message}`; return; }
    if (sectionsError) { status.textContent = `تعذر تحميل إعدادات الأقسام: ${sectionsError.message}. نفّذ ملف home_page_sections.sql أولاً.`; return; }
    const productOptions = (products || []).map(p => `<option value="${escapeHtml(p.id)}">${escapeHtml(p.name)} — ${escapeHtml(p.category || '')} — ${Number(p.price || 0).toFixed(2)} د.ل</option>`).join('');
    const savedMap = new Map((saved || []).map(row => [row.section_key, row]));
    host.innerHTML = SECTION_DEFS.map((def, index) => {
      const row = savedMap.get(def.key) || {};
      const selected = Array.isArray(row.product_ids) ? row.product_ids.map(String) : [];
      const options = (products || []).map(p => `<option value="${escapeHtml(p.id)}" ${selected.includes(String(p.id)) ? 'selected' : ''}>${escapeHtml(p.name)} — ${escapeHtml(p.category || '')} — ${Number(p.price || 0).toFixed(2)} د.ل</option>`).join('');
      return `<article class="hs-box" data-section="${def.key}">
        <h3>${def.title}</h3><p class="hs-meta">${def.description}</p>
        <label class="hs-toggle"><input class="hs-enabled" type="checkbox" ${row.is_enabled === false ? '' : 'checked'}> تفعيل ظهور القسم في الصفحة الرئيسية</label>
        <label>المنتجات (يمكن تحديد أكثر من منتج، والترتيب من الأعلى إلى الأسفل)
          <select class="hs-products" multiple>${options}</select>
        </label>
        <label>ترتيب القسم في الصفحة الرئيسية <input class="hs-order" type="number" min="0" step="1" value="${Number(row.sort_order ?? (index + 1) * 10)}"></label>
        <div class="hs-actions"><button type="button" class="hs-save">حفظ إعدادات هذا القسم</button><span class="hs-meta hs-message"></span></div>
      </article>`;
    }).join('');
    host.querySelectorAll('.hs-save').forEach(button => button.addEventListener('click', async () => {
      const box = button.closest('[data-section]');
      const key = box.dataset.section;
      const def = SECTION_DEFS.find(x => x.key === key);
      const ids = Array.from(box.querySelector('.hs-products').selectedOptions).map(o => o.value);
      const payload = {
        section_key: key,
        title: def.title,
        product_ids: ids,
        is_enabled: box.querySelector('.hs-enabled').checked,
        sort_order: Math.max(0, Number(box.querySelector('.hs-order').value || 0)),
        updated_at: new Date().toISOString()
      };
      const message = box.querySelector('.hs-message');
      button.disabled = true; message.textContent = 'جارٍ الحفظ...';
      const { error } = await sb.from('home_page_sections').upsert(payload, { onConflict: 'section_key' });
      button.disabled = false;
      message.textContent = error ? `فشل الحفظ: ${error.message}` : 'تم الحفظ. ستتحدث الصفحة الرئيسية تلقائياً.';
      message.style.color = error ? '#b42318' : '#16734a';
    }));
    status.textContent = `تم تحميل ${products?.length || 0} منتجاً و${SECTION_DEFS.length} أقسام قابلة للإدارة.`;
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();


// ASTRO MOBILE — إعداد صور الأقسام وطريقة عرض المنتجات داخل صفحة إدارة الأقسام الحالية.
(() => {
  const $ = (id) => document.getElementById(id);
  const esc = (v) => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const client = () => window.sb || window.supabaseClient;

  function initCategoryDesignControls() {
    const view = $('categories');
    if (!view || $('categoryDesignUnifiedPanel')) return;

    const panel = document.createElement('section');
    panel.id = 'categoryDesignUnifiedPanel';
    panel.className = 'category-design-panel';
    panel.innerHTML = `
      <h2>إعدادات الصور وطريقة العرض</h2>
      <p>تحكم في صور الأقسام وشعارات الشركات، واختر طريقة عرض المنتجات داخل التطبيق.</p>
      <div class="cd-settings">
        <h3>طريقة عرض المنتجات</h3>
        <form id="cdDisplayForm">
          <label>طريقة العرض الافتراضية
            <select id="cdLayout">
              <option value="grid">شبكي — بطاقات عمودية</option>
              <option value="list">قائمة — بطاقات أفقية</option>
            </select>
          </label>
          <label>عدد المنتجات في الصف
            <select id="cdColumns">
              <option value="2">منتجان</option>
              <option value="3">ثلاثة منتجات</option>
            </select>
          </label>
          <label class="cd-check">
            <input id="cdCustomerToggle" type="checkbox" checked>
            السماح للعميل بالتبديل بين العرضين
          </label>
          <button id="cdSaveSettings" type="submit">حفظ إعدادات العرض</button>
          <p id="cdSettingsMsg" role="status"></p>
        </form>
      </div>
      <div class="cd-images">
        <div class="cd-heading">
          <div><h3>صور الأقسام وشعارات الشركات</h3>
            <p>اختر القسم، وارفع الصورة الجديدة، ثم اضغط حفظ الصورة. يمكنك إزالة الصورة للعودة إلى الصورة الافتراضية.</p>
          </div>
          <button id="cdRefresh" type="button">تحديث القائمة</button>
        </div>
        <p id="cdImagesMsg" role="status">جارٍ تحميل الأقسام...</p>
        <div id="cdCategoryRows"></div>
      </div>`;
    const list = $('categoryList');
    if (list) list.insertAdjacentElement('afterend', panel);
    else view.append(panel);

    const style = document.createElement('style');
    style.textContent = `
      .category-design-panel{margin-top:18px;padding:16px;border:1px solid #d7e5f2;border-radius:14px;background:#f8fbff}
      .category-design-panel h2,.category-design-panel h3{color:#082c5c;margin:0 0 8px}
      .category-design-panel p{line-height:1.8}
      .cd-settings,.cd-images{background:#fff;border:1px solid #d7e5f2;border-radius:12px;padding:14px;margin:14px 0}
      .cd-check{display:flex;align-items:center;gap:8px}.cd-check input{width:auto}
      .cd-heading{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}
      .cd-row{display:grid;grid-template-columns:72px minmax(0,1fr);gap:12px;align-items:center;border:1px solid #d7e5f2;border-radius:12px;padding:12px;margin:10px 0}
      .cd-preview{width:68px;height:68px;object-fit:contain;background:#fff;border:1px solid #e1eaf3;border-radius:10px}
      .cd-row label{margin:7px 0}.cd-row input[type=file]{font-size:12px;padding:8px}
      .cd-actions{display:flex;gap:6px;flex-wrap:wrap}.cd-row button{font-size:12px;padding:9px 11px}
      .cd-muted{color:#66809a;font-size:12px}.cd-good{color:#16734a}.cd-error{color:#b42318}
      @media(max-width:420px){.cd-row{grid-template-columns:58px minmax(0,1fr);gap:8px;padding:9px}.cd-preview{width:56px;height:56px}}
    `;
    document.head.append(style);

    $('cdRefresh')?.addEventListener('click', loadCategories);
    $('cdDisplayForm')?.addEventListener('submit', saveDisplaySettings);
  }

  async function loadDisplaySettings() {
    const sb = client(), msg = $('cdSettingsMsg');
    if (!sb || !msg) return;
    msg.textContent = 'جارٍ تحميل الإعدادات...';
    const {data,error} = await sb.from('store_display_settings')
      .select('id,product_layout,grid_columns,allow_customer_toggle')
      .eq('id',1).maybeSingle();
    if (error) {
      msg.className = 'cd-error';
      msg.textContent = 'تعذر تحميل الإعدادات. نفّذ supabase/category_design_settings.sql أولاً: ' + error.message;
      return;
    }
    $('cdLayout').value = data?.product_layout || 'grid';
    $('cdColumns').value = String(data?.grid_columns || 2);
    $('cdCustomerToggle').checked = data?.allow_customer_toggle !== false;
    msg.className = 'cd-good';
    msg.textContent = 'تم تحميل إعدادات العرض الحالية.';
  }

  async function saveDisplaySettings(event) {
    event.preventDefault();
    const sb = client(), button = $('cdSaveSettings'), msg = $('cdSettingsMsg');
    if (!sb) { msg.textContent = 'تعذر الاتصال بقاعدة البيانات.'; msg.className = 'cd-error'; return; }
    button.disabled = true; msg.textContent = 'جارٍ حفظ الإعدادات...';
    try {
      const payload = {
        id:1, product_layout:$('cdLayout').value,
        grid_columns:Number($('cdColumns').value),
        allow_customer_toggle:$('cdCustomerToggle').checked,
        updated_at:new Date().toISOString()
      };
      const {error} = await sb.from('store_display_settings').upsert(payload,{onConflict:'id'});
      if (error) throw error;
      msg.className = 'cd-good';
      msg.textContent = 'تم حفظ الإعدادات. سيستقبل التطبيق التغيير عبر Supabase.';
    } catch (error) {
      msg.className = 'cd-error'; msg.textContent = 'تعذر الحفظ: ' + (error.message || error);
    } finally { button.disabled = false; }
  }

  async function loadCategories() {
    const sb = client(), host = $('cdCategoryRows'), msg = $('cdImagesMsg');
    if (!sb || !host || !msg) return;
    msg.textContent = 'جارٍ تحميل الأقسام...';
    const {data,error} = await sb.from('categories')
      .select('id,name,parent_id,image_url,sort_order,is_active')
      .order('sort_order',{ascending:true});
    if (error) {
      msg.className = 'cd-error';
      msg.textContent = 'تعذر تحميل الأقسام. تأكد من تنفيذ SQL لإضافة image_url: ' + error.message;
      return;
    }
    const rows = data || [], names = new Map(rows.map(r => [String(r.id),r.name]));
    host.innerHTML = rows.map(r => {
      const title = r.parent_id ? '↳ ' + (names.get(String(r.parent_id)) || 'قسم') + ' / ' + r.name : '📁 ' + r.name;
      const preview = r.image_url
        ? '<img class="cd-preview" src="' + esc(r.image_url) + '" alt="' + esc(r.name) + '">'
        : '<div class="cd-preview" style="display:grid;place-items:center;color:#087fe5;font-size:25px">▧</div>';
      return `<article class="cd-row" data-category-id="${esc(r.id)}">
        ${preview}<div><strong>${esc(title)}</strong>
        <div class="cd-muted">${r.is_active ? 'نشط' : 'متوقف'} — الترتيب ${Number(r.sort_order || 0)}</div>
        <label>اختيار صورة أو شعار<input class="cd-file" type="file" accept="image/*"></label>
        <div class="cd-actions"><button type="button" class="cd-save-image">حفظ الصورة</button><button type="button" class="cd-remove-image">إزالة الصورة</button></div>
        <span class="cd-muted cd-row-msg"></span></div></article>`;
    }).join('') || '<p>لا توجد أقسام مسجلة.</p>';
    host.querySelectorAll('.cd-save-image').forEach(b => b.addEventListener('click', () => saveCategoryImage(b)));
    host.querySelectorAll('.cd-remove-image').forEach(b => b.addEventListener('click', () => removeCategoryImage(b)));
    msg.className = 'cd-good'; msg.textContent = 'تم تحميل ' + rows.length + ' قسماً.';
  }

  async function saveCategoryImage(button) {
    const sb = client(), row = button.closest('[data-category-id]');
    const file = row.querySelector('.cd-file').files?.[0], msg = row.querySelector('.cd-row-msg');
    if (!file) { msg.textContent = 'اختر صورة أولاً.'; msg.className = 'cd-error'; return; }
    if (!file.type.startsWith('image/')) { msg.textContent = 'الملف المختار ليس صورة.'; msg.className = 'cd-error'; return; }
    if (file.size > 5*1024*1024) { msg.textContent = 'حجم الصورة أكبر من 5 ميغابايت.'; msg.className = 'cd-error'; return; }
    button.disabled = true; msg.textContent = 'جارٍ رفع الصورة...';
    try {
      const ext = (file.name.split('.').pop() || 'jpg').toLowerCase().replace(/[^a-z0-9]/g,'') || 'jpg';
      const path = 'category-images/' + row.dataset.categoryId + '/' + Date.now() + '-' + crypto.randomUUID() + '.' + ext;
      const {data:uploaded,error:uploadError} = await sb.storage.from('products')
        .upload(path,file,{cacheControl:'3600',upsert:false,contentType:file.type});
      if (uploadError) throw uploadError;
      const {data:publicData} = sb.storage.from('products').getPublicUrl(uploaded.path);
      const imageUrl = publicData?.publicUrl;
      if (!imageUrl) throw new Error('تعذر استخراج رابط الصورة بعد الرفع.');
      const {error:updateError} = await sb.from('categories').update({image_url:imageUrl}).eq('id',row.dataset.categoryId);
      if (updateError) throw updateError;
      msg.className = 'cd-good'; msg.textContent = 'تم رفع الصورة وربطها بالقسم.';
      await loadCategories();
    } catch (error) {
      msg.className = 'cd-error'; msg.textContent = 'فشل حفظ الصورة: ' + (error.message || error);
    } finally { button.disabled = false; }
  }

  async function removeCategoryImage(button) {
    const sb = client(), row = button.closest('[data-category-id]');
    const msg = row.querySelector('.cd-row-msg');
    if (!confirm('إزالة الصورة المخصصة؟ سيعود التطبيق إلى الصورة الافتراضية.')) return;
    button.disabled = true;
    try {
      const {error} = await sb.from('categories').update({image_url:null}).eq('id',row.dataset.categoryId);
      if (error) throw error;
      msg.className = 'cd-good'; msg.textContent = 'تمت إزالة الصورة المخصصة.';
      await loadCategories();
    } catch (error) {
      msg.className = 'cd-error'; msg.textContent = 'تعذر إزالة الصورة: ' + (error.message || error);
    } finally { button.disabled = false; }
  }

  function init() {
    initCategoryDesignControls();
    document.querySelector('nav button[data-view="categories"]')?.addEventListener('click', () => {
      loadDisplaySettings(); loadCategories();
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
