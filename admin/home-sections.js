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
