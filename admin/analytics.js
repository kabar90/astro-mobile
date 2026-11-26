
const astroAnalyticsClient = window.sb || window.supabaseClient;
const analytics$ = id => document.getElementById(id);
const analyticsSet = (id, value) => { const el=analytics$(id); if(el) el.textContent=Number(value||0).toLocaleString("en-US"); };

async function refreshAstroAnalytics() {
  const msg=analytics$("analyticsMsg");
  if(msg) msg.textContent="جارٍ تحميل الإحصائيات...";
  try {
    if(!astroAnalyticsClient) throw new Error("اتصال قاعدة البيانات غير جاهز.");
    const {data: events,error}=await astroAnalyticsClient
      .from("astro_analytics_events")
      .select("event_name,installation_id,user_id,source,created_at,metadata")
      .order("created_at",{ascending:false})
      .limit(10000);
    if(error) throw error;

    const {count: devices,error:deviceError}=await astroAnalyticsClient
      .from("astro_device_tokens")
      .select("id",{count:"exact",head:true});
    if(deviceError) throw deviceError;

    const rows=events||[];
    const count=name=>rows.filter(x=>x.event_name===name).length;
    const since7=Date.now()-7*24*60*60*1000;
    const recent=rows.filter(x=>new Date(x.created_at).getTime()>=since7);
    const countRecent=name=>recent.filter(x=>x.event_name===name).length;

    analyticsSet("anPageViews",count("download_page_view"));
    analyticsSet("anDownloadClicks",count("apk_download_click"));
    analyticsSet("anFirstOpens",new Set(rows.filter(x=>x.event_name==="app_first_open").map(x=>x.installation_id).filter(Boolean)).size);
    analyticsSet("anAccounts",count("account_created"));
    analyticsSet("anOrders",count("order_created"));
    analyticsSet("anDevices",devices||0);
    analyticsSet("an7Views",countRecent("download_page_view"));
    analyticsSet("an7Clicks",countRecent("apk_download_click"));
    analyticsSet("an7Opens",new Set(recent.filter(x=>x.event_name==="app_first_open").map(x=>x.installation_id).filter(Boolean)).size);
    analyticsSet("an7Accounts",countRecent("account_created"));
    if(analytics$("analyticsUpdated")) analytics$("analyticsUpdated").textContent="آخر تحديث: "+new Date().toLocaleString("ar-LY");
    if(msg) msg.textContent="تم تحديث الإحصائيات بنجاح.";
  } catch(error) {
    console.error("ASTRO analytics error:",error);
    if(msg) msg.textContent="تعذر تحميل الإحصائيات: "+(error.message||error);
  }
}
analytics$("refreshAnalytics")?.addEventListener("click",refreshAstroAnalytics);
window.ASTROAnalytics={refresh:refreshAstroAnalytics};
