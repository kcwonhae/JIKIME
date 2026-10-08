const ENDPOINT = "http://127.0.0.1:8765/api/event";

const isJikimeDashboard =
  (location.hostname === "127.0.0.1" || location.hostname === "localhost") &&
  location.port === "8765";

const isManualDemo = !!document.querySelector('meta[name="jikime-demo"][content="manual"]');

function visibleText(limit=4000){
  const bodyText = document.body ? document.body.innerText : "";
  return bodyText.replace(/\s+/g," ").slice(0,limit);
}

function sendEvent(eventType, extra={}){
  if(isJikimeDashboard) return;
  const payload = {
    event_type: eventType,
    url: location.href,
    title: document.title,
    text: visibleText(),
    timestamp: new Date().toISOString(),
    ...extra
  };
  fetch(ENDPOINT,{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify(payload)
  }).catch(()=>{});
}

if(!isJikimeDashboard && !isManualDemo){
  setTimeout(()=>sendEvent("page_view"),800);

  document.addEventListener("click",(e)=>{
    const a=e.target.closest("a");
    const btn=e.target.closest("button");
    if(a){
      sendEvent("link_click",{clicked_text:(a.innerText||"").slice(0,300),target_url:a.href||""});
    }else if(btn){
      sendEvent("button_click",{clicked_text:(btn.innerText||"").slice(0,300)});
    }
  },true);

  document.addEventListener("submit",(e)=>{
    sendEvent("form_submit",{form_action:e.target.action||""});
  },true);
}

// 데모 페이지에서는 페이지가 단계별 Agent 행동을 명시적으로 전달한다.
if(isManualDemo){
  window.addEventListener("message", (event) => {
    if(event.source !== window) return;
    if(!event.data || event.data.type !== "JIKIME_DEMO_EVENT") return;
    const p = event.data.payload || {};
    sendEvent(p.event_type || "demo_step", p);
  });
}
