const $=s=>document.querySelector(s),app=$("#app");
const API=window.HORIZON_API!==undefined?window.HORIZON_API:(location.protocol==="file:"?"http://127.0.0.1:8000":"");
const TAGS={"General Medicine":["Fever","Cough","Cold","Fatigue","Headache"],Cardiology:["Chest pain","Breathlessness","Palpitations","Dizziness"],Dermatology:["Rashes","Acne","Itching","Hair loss"],Orthopedics:["Joint pain","Back pain","Fracture","Stiffness"],Pediatrics:["Child fever","Vomiting","Diarrhea","Rashes"],Gastroenterology:["Stomach pain","Acidity","Constipation"],Urology:["Frequent urine","Kidney pain","Blood in urine"],Neurology:["Headache","Numbness","Seizures"],Dentistry:["Toothache","Gum bleeding","Cavity"]};
const RED=/chest pain|can.?t breathe|short of breath|breathless|unconscious|stroke|seizure|heavy bleeding|suicid|faint|सीने|सांस|बेहोश|বুকুত বিষ|উশাহ/i;
const SPEC=[[/chest|heart|bp|palpit|सीने|দিল|বুকু/i,"Cardiology"],[/skin|rash|acne|itch|hair|त्वचा|ছাল/i,"Dermatology"],[/knee|back|joint|bone|fracture|हड्डी|ঠেং|হাড়/i,"Orthopedics"],[/stomach|acid|vomit|digest|liver|पेट|পেট/i,"Gastroenterology"],[/child|baby|kid|बच्चा|শিশু/i,"Pediatrics"],[/urine|urinary|kidney/i,"Urology"],[/numb|seiz|migraine|tingling/i,"Neurology"],[/tooth|teeth|gum|dental/i,"Dentistry"]];
const GIVE={"O-":["O-"],"O+":["O+","O-"],"A-":["A-","O-"],"A+":["A+","A-","O+","O-"],"B-":["B-","O-"],"B+":["B+","B-","O+","O-"],"AB-":["AB-","A-","B-","O-"],"AB+":["O+","O-","A+","A-","B+","B-","AB+","AB-"]};
const NAV={patient:[["chat","Assistant"],["docs","Doctors"],["hosp","Hospitals"],["svc","Services"],["appts","Appointments"],["feed","Health"],["blood","Blood"]],doctor:[["dash","Dashboard"]],hospital:[["ref","Referrals"],["breq","Blood requests"]]};
const STL={new:["Waiting for doctor","am"],accepted:["Accepted","ok"],completed:["Completed","te"],cancelled:["Declined or cancelled","ur"],live:["Live","ok"]};
const S={role:null,name:"",tab:"",token:null,user_id:null,patient_id:null,doctor_id:null,hospital_id:null,approved:false,profile:null,loc:null,phone:"",lang:"en-IN",chat:[{w:"ai",t:"Hello, I’m the Blood Link assistant. Tell me how you feel in your own words, speak, or upload a report. I suggest a specialty and verified doctors. I can’t diagnose."}],files:[],blobs:[],docs:[],hospitals:[],labs:[],articles:[],cities:[],appts:[],refs:[],reqs:[],qa:[],notes:[],bl:[],don:{on:false,g:"O+",mail:""},dt:"new",unread:0,quality:null};
const KEYS=["token","role","name","phone","user_id","patient_id","doctor_id","hospital_id","approved","profile","loc","lang","chat"];
try{const d=JSON.parse(localStorage.getItem("hz")||"{}");KEYS.forEach(k=>{if(d[k]!==undefined)S[k]=d[k]})}catch(e){}
const save=()=>{try{localStorage.setItem("hz",JSON.stringify(Object.fromEntries(KEYS.map(k=>[k,S[k]]))))}catch(e){}};
setInterval(save,1000);addEventListener("pagehide",save);
const toast=m=>{const t=$("#toast");t.textContent=m;t.hidden=false;clearTimeout(toast.h);toast.h=setTimeout(()=>t.hidden=true,3200)};
const esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
function detail(raw){try{const j=JSON.parse(raw);const d=j.detail;if(typeof d==="string")return d;if(Array.isArray(d))return d.map(x=>x.msg||JSON.stringify(x)).join("; ");return raw}catch(e){return raw||"Request failed"}}
async function api(path,opts={}){
  const {method="GET",json,form}=opts;
  const headers={};
  if(S.token)headers["X-Session-Token"]=S.token;
  let body;
  if(json){headers["Content-Type"]="application/json";body=JSON.stringify(json)}
  if(form)body=form;
  const r=await fetch(API+path,{method,headers,body});
  if(r.status===401){S.token=null;S.role=null;S.profile=null;save();throw new Error("Please sign in again.")}
  const text=await r.text();
  if(!r.ok)throw new Error(detail(text));
  if(!text)return null;
  try{return JSON.parse(text)}catch(e){return text}
}
async function ensureCatalog(force){
  if(!force && S.docs.length)return;
  const c=await api("/catalog");
  S.docs=c.doctors||[];S.hospitals=c.hospitals||[];S.labs=c.labs||[];S.articles=c.articles||[];S.cities=c.cities||[];
}
async function measureNet(){
  try{
    const t0=performance.now();
    await fetch(API+"/network/ping");
    const latency=Math.max(performance.now()-t0,1);
    const t1=performance.now();
    const r=await fetch(API+"/network/blob");
    await r.arrayBuffer();
    const dt=Math.max(performance.now()-t1,1);
    const kbps=(32.768*8)/(dt/1000);
    return {bandwidth_kbps:Math.round(Math.min(Math.max(kbps,16),2000)),latency_ms:Math.round(latency),packet_loss:0};
  }catch(e){return {bandwidth_kbps:64,latency_ms:400,packet_loss:0.05}}
}
function go(t){S.tab=t;render()}
function logout(){hangup();stopLive();S.token=null;S.role=null;S.profile=null;S.docs=[];localStorage.removeItem("hz");render()}
async function render(){
  try{
    if(!S.token||!S.role)return login();
    try{
      applyUser(await api("/auth/me"));
    }catch(e){
      if(!S.token)return login();
      throw e;
    }
    await ensureCatalog(true).catch(()=>{});
    if(!S.profile)return onboard();
    shell();
  }catch(e){toast(e.message||"Couldn’t reach the Blood Link server. Start the backend on port 8000.")}
}
function login(){
  const R=[["patient","Patient","Find the right doctor"],["doctor","Doctor","Get verified, see requests"],["hospital","Hospital","Referrals and blood"]];
  app.innerHTML=`<section class="hero"><div class="sunb"></div><div class="hills"></div><div class="hin"><div class="brand">Blood Link</div><h1>Every drop has a destination.</h1><p>Blood Link matches verified donors with the people and hospitals who need them, and rewards the donors who keep showing up.</p>
<fieldset class="arches"><legend hidden>Choose your role</legend>${R.map((r,i)=>`<div class="role"><input type="radio" name="r" id="r${i}" value="${r[0]}" ${i?"":"checked"}><label for="r${i}"><b>${r[1]}</b><span class="mu">${r[2]}</span></label></div>`).join("")}</fieldset>
<form class="fm" id="lf" novalidate><label class="l" for="nm">Full name</label><input id="nm" autocomplete="name" value="${esc(S.name||"")}"><label class="l" for="mb">Mobile number</label><input id="mb" type="tel" inputmode="numeric" autocomplete="tel" placeholder="10-digit number" value="${esc(S.phone||"")}">
<div class="row" style="margin-top:12px"><button type="button" class="btn q s" id="lc">Share my location</button><span id="ls">${S.loc?"Location shared ✓":"Required"}</span></div><p class="err" id="er" role="alert"></p><button class="btn" id="go" style="width:100%">Log in</button></form></div></section>`;
  $("#lc").onclick=()=>{const t=$("#ls");if(!navigator.geolocation){t.textContent="Location isn’t supported on this device.";return}t.textContent="Finding you…";navigator.geolocation.getCurrentPosition(p=>{S.loc=p.coords.latitude.toFixed(4)+", "+p.coords.longitude.toFixed(4);t.textContent="Location shared ✓"},()=>{S.loc=null;t.textContent="Blocked. Allow location in your browser settings."},{timeout:10000})};
  $("#lf").onsubmit=async e=>{
    e.preventDefault();
    const nm=$("#nm").value.trim(),mb=$("#mb").value.replace(/[\s-]/g,"").replace(/^\+91/,""),er=$("#er");
    if(nm.length<3||!nm.includes(" "))return er.textContent="Enter your full name (first and last).";
    if(!/^[6-9]\d{9}$/.test(mb))return er.textContent="Enter a valid 10-digit mobile number.";
    if(!S.loc)return er.textContent="Location is required. Tap “Share my location”.";
    const role=document.querySelector("input[name=r]:checked").value;
    try{
      const data=await api("/auth/login",{method:"POST",json:{role,name:nm,phone:mb,location:S.loc}});
      applyUser(data);S.tab=NAV[role][0][0];render();
    }catch(err){er.textContent=err.message}
  };
}
function applyUser(data){
  S.token=data.token;S.user_id=data.user_id;S.role=data.role;S.name=data.name;S.phone=data.phone;
  S.location=data.location;S.loc=data.location||S.loc;S.approved=data.approved;
  S.doctor_id=data.doctor_id;S.patient_id=data.patient_id;S.hospital_id=data.hospital_id;
  S.profile=data.profile&&Object.keys(data.profile).length?data.profile:null;
  save();
}
function PF(){
  const specs=[...new Set((S.docs||[]).map(d=>d.specialty))];
  if(!specs.length)specs.push("General Medicine","Cardiology","Dermatology","Orthopedics","Pediatrics","Gastroenterology","Urology","Neurology","Dentistry");
  return {patient:[["age","Age","number"],["gender","Gender","select:Female,Male,Other"],["city","City or district","text"],["blood","Blood group","select:"+Object.keys(GIVE).join(",")+",Don’t know"],["ec","Emergency contact number","tel"]],
    doctor:[["reg","Medical registration number","text"],["spec","Specialty","select:"+specs.join(",")],["qual","Qualification (e.g. MBBS, MD)","text"],["inst","Institution","text"],["exp","Years of experience","number"],["city","City or district","text"]],
    hospital:[["hn","Hospital name","text"],["reg","Hospital registration number","text"],["city","City","text"],["addr","Address","text"],["desk","Front-desk phone","tel"]]};
}
function onboard(){
  const f=PF()[S.role];
  app.innerHTML=`<main style="padding-bottom:40px"><form class="card fm2" id="pf" novalidate><h2>One last step</h2><p class="mu">These details are required before you continue.${S.role==="doctor"?" Our team checks them by hand before you receive patient requests.":""}</p>${f.map(x=>`<label class="l" for="f_${x[0]}">${x[1]}</label>${x[2].startsWith("select")?`<select id="f_${x[0]}"><option value="">Choose…</option>${x[2].slice(7).split(",").map(o=>`<option>${o}</option>`).join("")}</select>`:`<input id="f_${x[0]}" type="${x[2]}">`}`).join("")}<p class="err" id="er" role="alert"></p><button class="btn" style="width:100%">Save and continue</button></form></main>`;
  $("#pf").onsubmit=async e=>{
    e.preventDefault();const p={};for(const x of f){const v=$("#f_"+x[0]).value.trim();if(!v){$("#f_"+x[0]).focus();return $("#er").textContent="Please fill in: "+x[1]+"."}p[x[0]]=v}
    if(p.age&&(p.age<1||p.age>120))return $("#er").textContent="Enter a valid age.";
    try{
      const data=await api("/auth/onboard",{method:"POST",json:{profile:p}});
      applyUser(data);toast("Welcome to Blood Link");render();
    }catch(err){$("#er").textContent=err.message}
  };
}
function shell(){
  const n=NAV[S.role];
  app.innerHTML=`<header class="ph"><span class="brand">Blood Link</span><svg class="ecg" viewBox="0 0 420 26" preserveAspectRatio="none" aria-hidden="true"><path d="M0 13H150l10-11 14 22 10-11H420"/></svg><span class="who"><button class="btn q s" id="lo">Log out</button><span>${esc(S.name)}</span></span></header><main id="v"></main><nav class="nav dock" aria-label="Main">${n.map(x=>`<button data-t="${x[0]}" ${S.tab===x[0]||(S.tab==="room"&&x[0]==="appts")?'aria-current="page"':""}>${x[1]}${x[0]==="blood"&&S.unread?` <span class="pill ur">${S.unread}</span>`:""}</button>`).join("")}</nav>`;
  $("#lo").onclick=logout;
  startLive();
  document.querySelectorAll(".nav button").forEach(b=>b.onclick=()=>{hangup();go(b.dataset.t)});
  const view={chat,docs,hosp,svc,feed,appts,blood,dash,ref,breq,room}[S.tab];
  Promise.resolve(view($("#v"))).catch(e=>toast(e.message||"Couldn’t load this screen."));
}
function analyze(t){const red=RED.test(t);let sp="General Medicine";for(const[r,s]of SPEC)if(r.test(t)){sp=s;break}
  const urgent=red||/severe|worst|high fever|unbearable|तेज़|ভীষণ/i.test(t);return{red,sp,urgent}}
function recs(sp,urgent){
  let l=S.docs.filter(d=>d.specialty===sp);if(!l.length)l=S.docs.filter(d=>d.specialty==="General Medicine");
  l=[...l].sort((a,b)=>urgent?(b.experience_years-a.experience_years):(a.fee-b.fee));
  const min=Math.min(...l.map(d=>d.fee),Infinity);
  return l.map(d=>({d,why:urgent?`Most experienced ${d.specialty.toLowerCase()} specialist (${d.experience_years} yrs) with the earliest slot ${d.slots[0]||""}.`:`${d.specialty} fits your description${d.fee===min?"; this is the lowest consultation fee for this specialty":""}.`}))
}
function chat(v){
  v.innerHTML=`<h2>Hi ${esc(S.name.split(" ")[0])}, how are you feeling?</h2><p class="mu">Type, speak or upload. Suggestions are not a diagnosis.</p><div class="tiles">${[["docs","Book a doctor"],["svc","Lab test"],["svc","Medicines"],["svc","Surgery help"],["hosp","Hospitals"]].map(t=>`<button data-g="${t[0]}">${t[1]}</button>`).join("")}</div><div class="card" style="margin-top:12px"><div class="chat" id="ch" aria-live="polite"></div>
<div class="row" style="margin-top:8px">${["Fever and cough","Skin rash","Knee pain","Stomach pain","Chest pain"].map(s=>`<button class="btn q s" data-s="${s}">${s}</button>`).join("")}</div>
<div id="fl" class="row mu"></div><div class="comp"><input type="text" id="ti" placeholder="Describe your symptoms…" aria-label="Describe your symptoms"><button class="btn q ib" id="mic" aria-label="Speak">🎤</button><label class="btn q ib" style="display:grid;place-items:center;cursor:pointer" aria-label="Upload file">📎<input type="file" id="up" multiple accept="image/*,.pdf" hidden></label><button class="btn" id="sd">Send</button></div>
<div class="row" style="margin-top:8px"><label for="lg" class="mu">Speech language</label><select id="lg" style="width:auto"><option value="en-IN">English</option><option value="hi-IN">हिन्दी</option><option value="as-IN">অসমীয়া</option></select></div></div>`;
  v.querySelectorAll("[data-g]").forEach(b=>b.onclick=()=>go(b.dataset.g));
  const ch=$("#ch");
  const draw=()=>{ch.innerHTML=S.chat.map(m=>m.h?`<div class="b ai">${m.h}</div>`:`<div class="b ${m.w}">${esc(m.t)}</div>`).join("");ch.scrollTop=1e9;
    $("#fl").innerHTML=S.files.map(f=>`<span class="pill te">📄 ${esc(f)}</span>`).join("");
    ch.querySelectorAll("[data-loc]").forEach(b=>b.onclick=share);
    ch.querySelectorAll("[data-bk]").forEach(b=>b.onclick=()=>prof(+b.dataset.bk))};
  draw();
  const send=t=>{t=t.trim();if(!t&&!S.files.length)return;S.chat.push({w:"me",t:t||"(shared a document)"});const a=analyze(t);
    if(a.red)S.chat.push({w:"ai",h:`<div class="em"><b class="ur">This may be an emergency.</b><p>Please get to the nearest hospital now, or ask someone nearby to take you. Don’t wait for a routine booking.</p><button class="btn d s" data-loc>Share my location with the nearest hospital</button></div>`});
    else{const rs=recs(a.sp,a.urgent);S.chat.push({w:"ai",h:`<p>From what you’ve said, <b>${a.sp}</b> looks like the right specialty${a.urgent?" and this seems fairly urgent, so I’m ranking by experience and earliest slot":", and I’m listing lower fees first"}. This is a suggestion, not a diagnosis.${S.files.length?" I can’t read your uploads; your doctor will see them if you share them when booking.":""}</p>${rs.slice(0,3).map(r=>`<div class="card" style="margin-top:8px"><b>${esc(r.d.name)}</b> <span class="pill ok">Verified</span><div class="mu">${esc(r.d.specialty)} · ₹${r.d.fee} · ★ ${r.d.rating}</div><p class="mu">${esc(r.why)}</p><button class="btn s" data-bk="${r.d.id}">View profile</button></div>`).join("")}`})}
    $("#ti").value="";draw()};
  $("#sd").onclick=()=>send($("#ti").value);$("#ti").onkeydown=e=>{if(e.key==="Enter")send(e.target.value)};
  v.querySelectorAll("[data-s]").forEach(b=>b.onclick=()=>send(b.dataset.s));
  $("#up").onchange=e=>{[...e.target.files].forEach(f=>{S.files.push(f.name);S.blobs.push(f)});draw();toast("Added. You choose what to share when booking.")};
  $("#lg").value=S.lang;$("#lg").onchange=e=>S.lang=e.target.value;
  $("#mic").onclick=()=>{const R=window.SpeechRecognition||window.webkitSpeechRecognition;if(!R)return toast("Voice input isn’t supported in this browser. Please type.");const r=new R();r.lang=S.lang;r.onresult=e=>{$("#ti").value=e.results[0][0].transcript;send($("#ti").value)};r.onerror=()=>toast("Couldn’t hear you. Check microphone permission.");r.start();toast("Listening…")};
}
async function share(){
  const send=async loc=>{
    S.loc=loc;
    await api("/referrals",{method:"POST",json:{from_text:"Patient emergency button",patient_name:S.name,note:"Self-reported emergency. No doctor consulted.",urgency:"Critical",location:loc}});
    S.chat.push({w:"ai",h:`<p>Location shared with <b>Sample City Hospital</b>. They can see where you are and respond. <b>Don’t wait. Get to the hospital now.</b> Status: <b>waiting for hospital</b>.</p>`});
    render();
  };
  if(S.loc)return send(S.loc);
  if(!navigator.geolocation)return send("Location unavailable. Hospital will call you.");
  navigator.geolocation.getCurrentPosition(p=>send(p.coords.latitude.toFixed(4)+", "+p.coords.longitude.toFixed(4)),()=>send("Location denied. Hospital will call you."),{timeout:8000});
}
function docs(v){
  const sp=[...new Set(S.docs.map(d=>d.specialty))];
  v.innerHTML=`<h2>Find a doctor</h2><div class="fb"><select id="fc" aria-label="City"><option value="">All cities</option>${S.cities.map(c=>`<option ${S.fc===c?"selected":""}>${esc(c)}</option>`).join("")}</select><input id="fq" type="search" placeholder="Search doctor, specialty or symptom" value="${esc(S.fq||"")}" aria-label="Search"></div><div class="tabs"><button data-sp="" aria-pressed="${!S.fsp}">All</button>${sp.map(s=>`<button data-sp="${s}" aria-pressed="${S.fsp===s}">${s}</button>`).join("")}</div><div class="dg" id="dl"></div>`;
  const draw=()=>{
    const q=(S.fq||"").toLowerCase();
    const L=S.docs.filter(d=>(!S.fc||d.city===S.fc)&&(!S.fsp||d.specialty===S.fsp)&&(!q||(d.name+d.specialty+(d.keywords||[]).join(" ")).toLowerCase().includes(q)));
    $("#dl").innerHTML=L.length?L.map(d=>`<article class="card"><b>${esc(d.name)}</b> <span class="pill ok">Verified</span><div class="mu">${esc(d.specialty)} · ${esc(d.city)} · ${d.experience_years} yrs · ${d.clinic_count} clinic(s)</div><div class="tg">${(d.keywords||[]).slice(0,4).map(k=>`<span>${esc(k)}</span>`).join("")}</div><div>₹${d.fee} · ★ ${d.rating} (${d.review_count})</div><div class="mu">${(d.modes||[]).join(", ")}</div><button class="btn s" style="margin-top:8px" data-p="${d.id}">View profile</button></article>`).join(""):`<div class="card mu">No doctors match. Try another city or clear the search.</div>`;
    v.querySelectorAll("[data-p]").forEach(b=>b.onclick=()=>prof(+b.dataset.p));
  };
  $("#fc").onchange=e=>{S.fc=e.target.value;draw()};$("#fq").oninput=e=>{S.fq=e.target.value;draw()};
  v.querySelectorAll("[data-sp]").forEach(b=>b.onclick=()=>{S.fsp=b.dataset.sp;docs(v)});draw();
}
function hosp(v){
  v.innerHTML=`<h2>Hospitals</h2><p class="mu">Partner hospitals across the region.</p><div class="fb"><select id="hc" aria-label="City"><option value="">All cities</option>${S.cities.map(c=>`<option ${S.hc===c?"selected":""}>${esc(c)}</option>`).join("")}</select></div><div class="dg">${S.hospitals.filter(h=>!S.hc||h.city===S.hc).map(h=>`<article class="card"><b>${esc(h.name)}</b><div class="mu">${esc(h.city)}</div><div class="tg">${(h.specialties||[]).map(x=>`<span>${esc(x)}</span>`).join("")}</div><button class="btn s" style="margin-top:8px" data-c="${esc(h.city)}">View doctors in ${esc(h.city)}</button></article>`).join("")}</div>`;
  $("#hc").onchange=e=>{S.hc=e.target.value;hosp(v)};v.querySelectorAll("[data-c]").forEach(b=>b.onclick=()=>{S.fc=b.dataset.c;S.fsp="";S.fq="";go("docs")});
}
function svc(v){
  v.innerHTML=`<h2>Services</h2><div class="dg"><section class="card"><h3>Book a lab test</h3>${S.labs.map((l,i)=>`<label class="l"><input type="checkbox" data-l="${i}" style="width:auto;min-height:0"> ${esc(l.name)} · ₹${l.price}</label>`).join("")}<label class="l"><input type="checkbox" id="hm" checked style="width:auto;min-height:0"> Home sample collection</label><button class="btn s" id="lb" style="margin-top:10px">Request lab test</button></section>
<section class="card"><h3>Order medicines</h3><label class="l" for="md">Medicines or prescription details</label><textarea id="md" rows="3" placeholder="e.g. Paracetamol 500 mg, 10 tablets"></textarea><button class="btn s" id="mb" style="margin-top:10px">Request order</button></section>
<section class="card"><h3>Surgery assistance</h3><label class="l" for="sg">Procedure or condition</label><input id="sg" placeholder="e.g. Knee replacement"><button class="btn s" id="sb" style="margin-top:10px">Request a call back</button></section></div>`;
  const add=async(kind,details,total="")=>{await api("/services",{method:"POST",json:{kind,details,total}});toast(kind+" requested");go("appts")};
  $("#lb").onclick=()=>{const c=[...v.querySelectorAll("[data-l]:checked")].map(x=>S.labs[x.dataset.l]);if(!c.length)return toast("Pick at least one test.");add("Lab test",c.map(x=>x.name).join(", ")+($("#hm").checked?" · home collection":" · at lab"),"₹"+c.reduce((a,x)=>a+x.price,0))};
  $("#mb").onclick=()=>{const t=$("#md").value.trim();if(!t)return toast("Add the medicines you need.");add("Medicines",t)};
  $("#sb").onclick=()=>{const t=$("#sg").value.trim();if(!t)return toast("Tell us the procedure.");add("Surgery assistance",t)};
}
async function feed(v){
  const mine=await api("/questions");
  v.innerHTML=`<h2>Health feed</h2><p class="mu">General information, not medical advice.</p><div class="grid" style="margin-top:12px">${S.articles.map(a=>`<details class="card"><summary><b>${esc(a.title)}</b></summary><p>${esc(a.body)}</p></details>`).join("")}</div>
<section class="card" style="margin-top:16px"><h3>Ask a specialist</h3><label class="l" for="qs">Specialty</label><select id="qs">${[...new Set(S.docs.map(d=>d.specialty))].map(x=>`<option>${esc(x)}</option>`).join("")}</select><label class="l" for="qt">Your question</label><textarea id="qt" rows="3"></textarea><button class="btn s" id="qb" style="margin-top:10px">Submit question</button></section>
<div class="grid" style="margin-top:12px">${(mine||[]).map(q=>`<article class="card"><b>${esc(q.s)}</b><p>${esc(q.t)}</p><span class="pill am">Waiting for a specialist</span></article>`).join("")}</div>`;
  $("#qb").onclick=async()=>{const t=$("#qt").value.trim();if(t.length<10)return toast("Write a bit more about your question.");await api("/questions",{method:"POST",json:{specialty:$("#qs").value,body:t}});toast("Question sent");feed(v)};
}
function prof(id){
  const d=S.docs.find(x=>x.id===id);if(!d)return toast("Doctor not found");
  let sl=(d.slots&&d.slots[0])||"10:00",md=(d.modes&&d.modes[0])||"Video";
  const m=document.createElement("div");m.className="modal";m.setAttribute("role","dialog");m.setAttribute("aria-modal","true");
  m.innerHTML=`<div class="card"><h2>${esc(d.name)}</h2><span class="pill ok">Verified by Horizon team</span><p>${esc(d.bio)}</p><p class="mu">${esc(d.qualification)} · ${esc(d.institution)} · ${d.experience_years} years · Speaks ${(d.languages||[]).join(", ")}</p><p>₹${d.fee} · ★ ${d.rating} from ${d.review_count} completed consultations</p>
<label class="l">Consultation type</label><div class="slots" id="md">${(d.modes||["Video"]).map((x,k)=>`<button data-v="${esc(x)}" aria-pressed="${!k}">${esc(x)}</button>`).join("")}</div>
<label class="l">Today’s slots</label><div class="slots" id="sl">${(d.slots||["10:00"]).map((x,k)=>`<button data-v="${esc(x)}" aria-pressed="${!k}">${esc(x)}</button>`).join("")}</div>
<label class="l" for="rs">Reason for visit</label><input id="rs" placeholder="e.g. Fever for 3 days">
${S.files.length?`<label class="l"><input type="checkbox" id="sf" checked style="width:auto;min-height:0"> Share ${S.files.length} uploaded file(s) with this doctor</label>`:""}
<div class="row" style="margin-top:14px"><button class="btn" id="bk">Request appointment</button><button class="btn q" id="cl">Close</button></div></div>`;
  document.body.appendChild(m);
  const pick=(id,set)=>m.querySelectorAll(`#${id} button`).forEach(b=>b.onclick=()=>{m.querySelectorAll(`#${id} button`).forEach(x=>x.setAttribute("aria-pressed","false"));b.setAttribute("aria-pressed","true");set(b.dataset.v)});
  pick("md",v=>md=v);pick("sl",v=>sl=v);
  m.querySelector("#cl").onclick=()=>m.remove();
  m.querySelector("#bk").onclick=async()=>{
    try{
      const net=await measureNet();
      const share=$("#sf")&&$("#sf").checked;
      const names=share?[...S.files]:[];
      const appt=await api("/consultations",{method:"POST",json:{doctor_id:d.id,symptoms:$("#rs").value||"General consultation",consult_type:md,slot_time:sl,files:names,...net}});
      if(share&&S.blobs.length){
        for(const file of S.blobs){
          const form=new FormData();form.append("file",file);form.append("consultation_id",appt.id);form.append("bandwidth_kbps",net.bandwidth_kbps);
          await api("/records",{method:"POST",form});
        }
      }
      m.remove();toast("Request sent to "+d.name);go("appts");
    }catch(e){toast(e.message)}
  };
}
async function appts(v){
  const [mine,reqs,refs]=await Promise.all([api("/consultations"),api("/services"),api("/referrals")]);
  S.appts=mine||[];S.reqs=reqs||[];S.refs=refs||[];
  v.innerHTML=`<h2>Your appointments</h2><div class="grid" style="margin-top:12px">${S.appts.length?S.appts.map(a=>{const r=S.refs.find(x=>x.aid===a.id);const st=STL[a.status]||STL.new;return`<article class="card"><b>${esc(a.doctor_name)}</b> <span class="pill ${st[1]}">${st[0]}</span><div class="mu">Today ${esc(a.slot_time)} · ${esc(a.consult_type)} · ${esc(a.symptoms)}</div><div class="mu">Link: ${esc(a.mode)} · ${esc(a.quality_profile)}</div>${r?`<p>Hospital referral: <b>${r.st==="new"?"waiting for hospital":r.st}</b>${r.a?" · ambulance assigned":""}</p>`:""}${(a.status==="accepted"||a.status==="live")&&a.consult_type!=="In person"?`<button class="btn s" data-j="${a.id}">${a.status==="live"?"Rejoin consultation":"Join waiting room"}</button>`:""}</article>`}).join(""):`<div class="card mu">No appointments yet. Ask the assistant or browse doctors.</div>`}</div>
<h3 style="margin-top:20px">Lab tests, medicines and more</h3><div class="grid" style="margin-top:8px">${S.reqs.length?S.reqs.map(r=>`<article class="card"><b>${esc(r.k)}</b> <span class="pill am">${esc(r.st||"Requested")}</span><div class="mu">${esc(r.d)} ${r.t?"· "+esc(r.t):""}</div></article>`).join(""):`<div class="card mu">Nothing requested yet. Try Services.</div>`}</div>`;
  v.querySelectorAll("[data-j]").forEach(b=>b.onclick=()=>{S.rm={id:+b.dataset.j,ph:"wait",mic:true,cam:true};go("room")});
}
async function blood(v){
  const [donor,notes]=await Promise.all([api("/blood/donor"),api("/blood/notes")]);
  S.don=donor;S.notes=notes.notes||[];S.unread=0;paintUnread();
  const d=S.don;
  v.innerHTML=`<h2>Blood donation</h2><p class="mu">Donation is voluntary and unpaid. Hospitals never see your phone number unless you accept a request.</p>
<div class="card" style="margin-top:12px"><h3>Donor profile</h3><label class="l" for="bg">Blood group</label><select id="bg">${Object.keys(GIVE).map(g=>`<option ${g===d.g?"selected":""}>${g}</option>`).join("")}</select><label class="l" for="em">Email for alerts</label><input id="em" type="email" value="${esc(d.mail)}" placeholder="you@gmail.com">
<p class="mu">Usual rules: age 18–65, at least 45 kg, a gap of 3 months (men) or 4 months (women) between donations. The blood bank makes the final call. Confirm figures with NBTC guidance.</p>
<label class="l"><input type="checkbox" id="cn" ${d.on?"checked":""} style="width:auto;min-height:0"> I agree to receive blood requests and share my details only when I accept</label><button class="btn" id="sv" style="margin-top:8px">${d.on?"Update availability":"Register as donor"}</button> ${d.on?`<button class="btn q" id="ps">Pause</button>`:""}</div>
<p style="margin-top:12px"><a href="https://eraktkosh.mohfw.gov.in" target="_blank" rel="noopener" class="te"><b>Check blood bank stock on e-RaktKosh</b></a></p>
<h3 style="margin-top:16px">Notifications</h3><div class="grid" style="margin-top:8px">${S.notes.length?S.notes.map(n=>`<article class="card"><b class="ur">${esc(n.u)} · ${esc(n.g)} needed</b><div>${esc(n.h)} · ${esc(n.c)} · ${n.n} unit(s)</div>${n.ok?`<span class="pill ok">You’re on your way. Desk: 0361-000-0000 (sample)</span>`:`<button class="btn s" data-y="${n.id}">I can donate</button>`}
<details style="margin-top:8px"><summary class="mu">Email preview</summary><div class="mu" style="margin-top:6px;white-space:pre-line">To: ${esc(d.mail||"your email")}\nSubject: ${esc(n.u)} ${esc(n.g)} blood needed at ${esc(n.h)}\nA patient at ${esc(n.h)}, ${esc(n.c)}, needs ${n.n} unit(s). Open Blood Link and tap “I can donate”.</div></details></article>`).join(""):`<div class="card mu">No requests right now.</div>`}</div>`;
  $("#sv").onclick=async()=>{if(!$("#cn").checked)return toast("Please tick the consent box.");const m=$("#em").value.trim();if(!/^\S+@\S+\.\S+$/.test(m))return toast("Enter a valid email.");await api("/blood/donor",{method:"POST",json:{blood_group:$("#bg").value,email:m,active:true}});toast("You’re registered as a donor");blood(v)};
  const p=$("#ps");if(p)p.onclick=async()=>{await api("/blood/donor",{method:"POST",json:{blood_group:$("#bg").value,email:$("#em").value,active:false}});toast("Paused. No alerts will be sent.");blood(v)};
  v.querySelectorAll("[data-y]").forEach(b=>b.onclick=async()=>{await api(`/blood/notes/${b.dataset.y}/accept`,{method:"POST"});toast("The hospital has been told you’re coming");blood(v)});
}
async function dash(v){
  if(!S.approved){
    v.innerHTML=`<div class="card" style="max-width:560px"><span class="pill am">Verification in review</span><h2 style="margin-top:8px">Your credentials are being checked</h2><p class="mu">Our team reviews degrees and registration by hand and may contact your institution. You’ll see patient requests only after approval.</p><ul class="mu"><li>Profile details: submitted</li><li>Degree certificates: in review</li><li>Registration number: in review</li></ul><button class="btn q" id="ap">Reviewer action: approve this doctor</button></div>`;
    $("#ap").onclick=async()=>{const data=await api("/auth/approve",{method:"POST"});applyUser(data);toast("Approved");render()};return;
  }
  const all=await api("/consultations");
  S.appts=all||[];
  const L=S.appts.filter(a=>S.dt==="accepted"?a.status==="accepted"||a.status==="live":a.status===S.dt);
  v.innerHTML=`<h2>Welcome, ${esc(S.name)} <span class="pill ok">Verified</span></h2><div class="row" style="margin-top:8px"><span class="card">★ ${(S.docs.find(d=>d.id===S.doctor_id)||{}).rating||4.8} rating</span><span class="card">${S.appts.filter(a=>a.status==="completed").length} consultations</span><span class="card">Adaptive link ready</span></div><p class="mu">Ratings and points never affect clinical urgency or ranking of emergencies.</p>
<div class="tabs" role="group" aria-label="Filter">${[["new","New requests"],["accepted","Accepted"],["completed","Completed"],["cancelled","Cancelled"]].map(t=>`<button data-f="${t[0]}" aria-pressed="${S.dt===t[0]}">${t[1]} (${S.appts.filter(a=>t[0]==="accepted"?a.status==="accepted"||a.status==="live":a.status===t[0]).length})</button>`).join("")}</div>
<div class="grid">${L.length?L.map(a=>`<article class="card"><b>${esc(a.patient_name)}</b> <span class="mu">${esc(a.slot_time)} · ${esc(a.consult_type)}</span><p>${esc(a.symptoms)}</p>${(a.files||[]).length?`<div class="mu">Shared: ${a.files.map(esc).join(", ")}</div>`:""}<div class="mu">${esc(a.mode)} · ${esc(a.quality_profile)}</div><div class="row">${a.status==="new"?`<button class="btn s" data-a="${a.id}">Accept</button><button class="btn q s" data-x="${a.id}">Decline</button>`:""}${a.status==="accepted"||a.status==="live"?`<button class="btn s" data-j="${a.id}">${a.status==="live"?"Rejoin":"Start consultation"}</button>`:""}</div></article>`).join(""):`<div class="card mu">Nothing here yet.</div>`}</div>`;
  v.querySelectorAll("[data-f]").forEach(b=>b.onclick=()=>{S.dt=b.dataset.f;dash(v)});
  v.querySelectorAll("[data-a]").forEach(b=>b.onclick=async()=>{await api(`/consultations/${b.dataset.a}`,{method:"PATCH",json:{status:"accepted"}});toast("Accepted");dash(v)});
  v.querySelectorAll("[data-x]").forEach(b=>b.onclick=async()=>{await api(`/consultations/${b.dataset.x}`,{method:"PATCH",json:{status:"cancelled"}});toast("Declined");dash(v)});
  v.querySelectorAll("[data-j]").forEach(b=>b.onclick=()=>{S.rm={id:+b.dataset.j,ph:"wait",mic:true,cam:true};go("room")});
}
let pc=null,localStream=null,signalWS=null,pollTimer=null,chatPoll=null,seenSignals=0,quality=null,liveTimer=null;
function stopLive(){if(liveTimer){clearInterval(liveTimer);liveTimer=null}}
function paintUnread(){
  const btn=document.querySelector('.nav [data-t="blood"]');
  if(!btn)return;
  btn.innerHTML=S.unread?`Blood <span class="pill ur">${S.unread}</span>`:"Blood";
}
function startLive(){
  stopLive();
  liveTimer=setInterval(async()=>{
    if(!S.token||document.querySelector(".modal")||S.tab==="room")return;
    try{
      if(S.role==="patient"){
        const n=await api("/blood/notes?peek=true");
        const u=n.unread||0;
        if(u!==S.unread){S.unread=u;paintUnread()}
      }
      const v=$("#v");if(!v)return;
      if(S.tab==="appts"){
        const rows=await api("/consultations");
        const sig=JSON.stringify((rows||[]).map(x=>[x.id,x.status]));
        if(sig!==S._apptSig){S._apptSig=sig;await appts(v)}
      }else if(S.tab==="dash"&&S.approved){
        const rows=await api("/consultations");
        const sig=JSON.stringify((rows||[]).map(x=>[x.id,x.status]));
        if(sig!==S._dashSig){S._dashSig=sig;await dash(v)}
      }else if(S.tab==="ref"){
        const rows=await api("/referrals");
        const sig=JSON.stringify((rows||[]).map(x=>[x.id,x.st,x.a]));
        if(sig!==S._refSig){S._refSig=sig;await ref(v)}
      }
    }catch(e){}
  },8000);
}
function hangup(){
  if(pollTimer){clearInterval(pollTimer);pollTimer=null}
  if(chatPoll){clearInterval(chatPoll);chatPoll=null}
  if(signalWS){try{signalWS.close()}catch(e){}signalWS=null}
  if(localStream){localStream.getTracks().forEach(t=>t.stop());localStream=null}
  if(pc){try{pc.close()}catch(e){}pc=null}
  quality=null;seenSignals=0;
}
function wsUrl(id){
  const base=API||location.origin;
  const u=new URL(base,location.href);
  u.protocol=u.protocol==="https:"?"wss:":"ws:";
  u.pathname=`/ws/consultations/${id}`;
  u.search="";u.hash="";
  return u.toString();
}
function sendSignal(id,obj){
  obj.sender_id=S.user_id;
  const text=JSON.stringify(obj);
  if(signalWS&&signalWS.readyState===1)signalWS.send(text);
  api("/signaling",{method:"POST",json:{consultation_id:id,event_type:obj.type||"signal",payload:text}}).catch(()=>{});
}
async function attachMedia(a){
  const video=a.consult_type==="Video"&&(!quality||quality.mode==="video");
  const audio=a.consult_type!=="In person"&&(!quality||!quality.use_store_and_forward);
  if(!video&&!audio)return;
  try{
    localStream=await navigator.mediaDevices.getUserMedia({audio:!!audio,video:video?{width:{ideal:quality&&quality.resolution?+quality.resolution.split("x")[0]:320},frameRate:{ideal:quality?quality.fps:12,max:15}}:false});
  }catch(e){toast("Camera or microphone blocked. You can still use chat.")}
}
async function ensurePC(id){
  if(pc)return pc;
  pc=new RTCPeerConnection({iceServers:[{urls:"stun:stun.l.google.com:19302"}]});
  if(localStream)localStream.getTracks().forEach(t=>pc.addTrack(t,localStream));
  pc.onicecandidate=e=>{if(e.candidate)sendSignal(id,{type:"ice",candidate:e.candidate})};
  pc.ontrack=e=>{const el=$("#remote");if(el)el.srcObject=e.streams[0]};
  if(quality&&quality.max_video_bitrate_kbps){
    const sender=pc.getSenders().find(s=>s.track&&s.track.kind==="video");
    if(sender){const p=sender.getParameters();if(!p.encodings||!p.encodings.length)p.encodings=[{}];p.encodings[0].maxBitrate=quality.max_video_bitrate_kbps*1000;sender.setParameters(p).catch(()=>{})}
  }
  return pc;
}
async function handleSignal(id,msg,isDoctor){
  if(!msg||!msg.type)return;
  if(msg.sender_id&&msg.sender_id===S.user_id)return;
  if(msg.type==="peer_left")return toast("The other person left");
  const conn=await ensurePC(id);
  if(msg.type==="offer"&&!isDoctor){
    await conn.setRemoteDescription(msg.sdp);
    const answer=await conn.createAnswer();
    await conn.setLocalDescription(answer);
    sendSignal(id,{type:"answer",sdp:conn.localDescription});
    if(S.rm&&S.rm.ph==="wait"){S.rm.ph="live";room($("#v"))}
  }else if(msg.type==="answer"&&isDoctor){
    if(!conn.currentRemoteDescription)await conn.setRemoteDescription(msg.sdp);
  }else if(msg.type==="ice"&&msg.candidate){
    try{await conn.addIceCandidate(msg.candidate)}catch(e){}
  }
}
function connectSignals(id,isDoctor){
  try{
    signalWS=new WebSocket(wsUrl(id));
    signalWS.onmessage=ev=>{try{handleSignal(id,JSON.parse(ev.data),isDoctor)}catch(e){}};
    signalWS.onerror=()=>{};
  }catch(e){}
  pollTimer=setInterval(async()=>{
    try{
      const events=await api(`/signaling/${id}`);
      for(const ev of events||[]){
        if(ev.id<=seenSignals)continue;seenSignals=ev.id;
        try{handleSignal(id,JSON.parse(ev.payload),isDoctor)}catch(e){}
      }
    }catch(e){}
  },2500);
}
async function startCall(id,isDoctor){
  await ensurePC(id);
  if(isDoctor){
    const offer=await pc.createOffer();
    await pc.setLocalDescription(offer);
    sendSignal(id,{type:"offer",sdp:pc.localDescription});
  }
}
async function room(v){
  const r=S.rm,doc=S.role==="doctor";
  const a=await api(`/consultations/${r.id}`);
  if(r.ph==="end"){
    hangup();
    if(doc){
      v.innerHTML=`<div class="card" style="max-width:480px"><h2>Consultation ended</h2><label class="l" for="nt">Clinical notes</label><textarea id="nt" rows="4" placeholder="Optional notes for the record">${esc(a.notes||"")}</textarea><button class="btn" id="dn" style="margin-top:10px">Save and complete</button></div>`;
      $("#dn").onclick=async()=>{await api(`/consultations/${a.id}`,{method:"PATCH",json:{status:"completed",notes:$("#nt").value}});toast("Consultation completed");go("dash")};
      return;
    }
    v.innerHTML=`<div class="card" style="max-width:480px"><h2>Consultation ended</h2><p class="mu">How was it?</p><div class="row" id="st">${[1,2,3,4,5].map(n=>`<button class="btn q" data-n="${n}" aria-label="${n} star">${"★".repeat(n)}</button>`).join("")}</div><button class="btn" id="dn" style="margin-top:10px">Submit</button></div>`;
    let n=5;v.querySelectorAll("[data-n]").forEach(b=>b.onclick=()=>{n=+b.dataset.n;toast(n+" star(s) selected")});
    $("#dn").onclick=async()=>{try{await api(`/consultations/${a.id}/rate`,{method:"POST",json:{rating:n}})}catch(e){await api(`/consultations/${a.id}`,{method:"PATCH",json:{status:"completed"}})}toast("Thanks for your feedback");go("appts")};return;
  }
  if(!quality){
    const net=await measureNet();
    quality=await api("/network/probe",{method:"POST",json:{consultation_id:a.id,...net}});
    S.quality=quality;
  }
  const chatMode=quality&&(quality.use_store_and_forward||quality.mode==="chat_only"||quality.mode==="store_and_forward");
  const title=r.ph==="wait"?"Waiting room":"Live consultation";
  let recs=[];try{recs=await api(`/records/consultation/${a.id}`)}catch(e){recs=[]}
  const fileHtml=recs.length?recs.map(f=>`<a href="${API}/records/${f.id}/download?session_token=${encodeURIComponent(S.token)}" target="_blank" rel="noopener">${esc(f.original_name)}</a>`).join(" · "):(a.files||[]).map(esc).join(", ");
  v.innerHTML=`<h2>${title}: ${esc(doc?a.patient_name:a.doctor_name)}</h2><p class="mu">${esc(a.consult_type)} · ${esc(a.slot_time)} · ${esc(quality?quality.quality_profile:a.quality_profile)}</p>
${quality?`<p class="mu">${esc(quality.reason)}</p>`:""}
${chatMode?`<div class="card" style="margin-top:10px"><div class="chat" id="cmbox"></div><div class="comp"><input id="mt" placeholder="Message (store-and-forward if the link drops)"><button class="btn" id="ms">Send</button></div></div>`:`<div class="vid" style="margin-top:10px"><video id="remote" autoplay playsinline></video><video id="local" class="local" autoplay playsinline muted></video></div>`}
<div class="row" style="margin-top:10px">${r.ph==="wait"?`<button class="btn" id="en">${doc?"Admit patient":"I’m ready"}</button>`:`<button class="btn q" id="mc" aria-pressed="${r.mic}">${r.mic?"Mute":"Unmute"}</button><button class="btn q" id="cm">${r.cam?"Camera off":"Camera on"}</button><button class="btn d" id="ed">End</button>`}${doc&&r.ph==="live"?`<button class="btn q" id="rf">Refer to hospital</button>`:""}</div>${fileHtml?`<div class="card" style="margin-top:12px"><b>Documents shared</b><div class="mu">${fileHtml}</div></div>`:""}`;
  if(!chatMode){
    if(!localStream)await attachMedia(a);
    const local=$("#local");if(local&&localStream)local.srcObject=localStream;
  }
  if(!signalWS)connectSignals(a.id,doc);
  if(chatMode){
    const box=$("#cmbox");
    const draw=async()=>{const msgs=await api(`/consultations/${a.id}/messages`);if(!box)return;box.innerHTML=(msgs||[]).map(m=>`<div class="b ${m.sender_role===S.role?"me":"ai"}">${esc(m.body)}</div>`).join("");box.scrollTop=1e9};
    draw();
    if(chatPoll)clearInterval(chatPoll);
    chatPoll=setInterval(draw,3000);
    if($("#ms"))$("#ms").onclick=async()=>{const t=$("#mt").value.trim();if(!t)return;await api(`/consultations/${a.id}/messages`,{method:"POST",json:{sender_role:S.role,body:t}});$("#mt").value="";draw()};
  }
  const q=id=>document.getElementById(id);
  if(q("en"))q("en").onclick=async()=>{r.ph="live";if(!chatMode)await startCall(a.id,doc);await api(`/consultations/${a.id}`,{method:"PATCH",json:{status:"live"}});room(v)};
  if(q("mc"))q("mc").onclick=()=>{r.mic=!r.mic;if(localStream)localStream.getAudioTracks().forEach(t=>t.enabled=r.mic);room(v)};
  if(q("cm"))q("cm").onclick=()=>{r.cam=!r.cam;if(localStream)localStream.getVideoTracks().forEach(t=>t.enabled=r.cam);room(v)};
  if(q("ed"))q("ed").onclick=()=>{r.ph="end";quality=null;room(v)};
  if(q("rf"))q("rf").onclick=()=>{
    const m=document.createElement("div");m.className="modal";
    m.innerHTML=`<div class="card"><h2>Refer to hospital</h2><label class="l" for="un">Urgency</label><select id="un"><option>Urgent</option><option>Within 24 hours</option><option>Routine</option></select><label class="l" for="nt">Note for the hospital</label><textarea id="nt" rows="3"></textarea><label class="l"><input type="checkbox" id="ck" style="width:auto;min-height:0"> The patient agreed to share their location</label><div class="row" style="margin-top:12px"><button class="btn" id="ok">Send referral</button><button class="btn q" id="no">Cancel</button></div></div>`;
    document.body.appendChild(m);
    m.querySelector("#no").onclick=()=>m.remove();
    m.querySelector("#ok").onclick=async()=>{
      if(!m.querySelector("#ck").checked)return toast("Location is shared only with patient consent.");
      await api("/referrals",{method:"POST",json:{from_text:a.doctor_name,patient_name:a.patient_name,note:m.querySelector("#nt").value||"Needs physical examination.",urgency:m.querySelector("#un").value,location:S.loc||"Patient location: hospital will confirm by phone",appointment_id:a.id}});
      m.remove();toast("Referral sent to Sample City Hospital");
    };
  };
}
async function ref(v){
  const rows=await api("/referrals");
  v.innerHTML=`<h2>Incoming referrals</h2><div class="grid" style="margin-top:12px">${rows.length?rows.map(r=>`<article class="card"><b>${esc(r.p)}</b> <span class="pill ${r.u==="Critical"||r.u==="Urgent"?"ur":"am"}">${esc(r.u)}</span> <span class="pill ${r.st==="accepted"?"ok":"am"}">${r.st==="new"?"New":esc(r.st)}</span><div class="mu">From: ${esc(r.from)}</div><p>${esc(r.note)}</p><div class="mu">📍 ${esc(r.loc)}</div>${r.a?`<p class="ok"><b>Ambulance ${esc(r.a)} assigned</b></p>`:""}<div class="row">${r.st==="new"?`<button class="btn s" data-a="${r.id}">Accept</button><button class="btn q s" data-d="${r.id}">Decline</button>`:""}${r.st==="accepted"&&!r.a?`<button class="btn s" data-m="${r.id}">Assign ambulance</button>`:""}</div></article>`).join(""):`<div class="card mu">No referrals yet. Referrals from doctors and the patient emergency button appear here.</div>`}</div>`;
  v.querySelectorAll("[data-a]").forEach(b=>b.onclick=async()=>{await api(`/referrals/${b.dataset.a}`,{method:"PATCH",json:{status:"accepted"}});ref(v)});
  v.querySelectorAll("[data-d]").forEach(b=>b.onclick=async()=>{await api(`/referrals/${b.dataset.d}`,{method:"PATCH",json:{status:"declined"}});ref(v)});
  v.querySelectorAll("[data-m]").forEach(b=>b.onclick=async()=>{await api(`/referrals/${b.dataset.m}`,{method:"PATCH",json:{status:"accepted",ambulance:"AMB-"+(100+(+b.dataset.m))}});toast("Ambulance assigned");ref(v)});
}
async function breq(v){
  const rows=await api("/blood/requests");
  v.innerHTML=`<h2>Blood requests</h2><div class="card" style="margin-top:12px"><label class="l" for="bg">Blood group needed</label><select id="bg">${Object.keys(GIVE).map(g=>`<option ${g==="O+"?"selected":""}>${g}</option>`).join("")}</select><label class="l" for="un">Units</label><input id="un" type="number" min="1" value="2"><label class="l" for="ur">Urgency</label><select id="ur"><option>Critical</option><option>Within 24 hours</option><option>Planned</option></select><label class="l" for="ct">City</label><input id="ct" value="Guwahati"><button class="btn" id="po" style="margin-top:12px">Post request</button></div>
<h3 style="margin-top:16px">Your requests</h3><div class="grid" style="margin-top:8px">${rows.length?rows.map(r=>`<article class="card"><b>${esc(r.g)}</b> · ${r.n} unit(s) · ${esc(r.u)}<div class="mu">${r.k} matching donors notified by app and email</div>${r.res.length?r.res.map(x=>`<div class="ok">Donor (${esc(x.g)}) on the way, ${esc(x.eta)}</div>`).join(""):`<div class="mu">No responders yet.</div>`}</article>`).join(""):`<div class="card mu">No requests posted.</div>`}</div>`;
  $("#po").onclick=async()=>{const n=+$("#un").value;if(!(n>0))return toast("Enter at least 1 unit.");await api("/blood/requests",{method:"POST",json:{blood_group:$("#bg").value,units:n,urgency:$("#ur").value,city:$("#ct").value||"Guwahati"}});toast("Request posted. Matching donors notified.");breq(v)};
}
render();
