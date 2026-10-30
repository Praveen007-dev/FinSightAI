"""FinSight AI web application.

FastAPI serves a lightweight browser UI so the research pipeline is not tied to
Streamlit's runtime or widget reruns.
"""

import asyncio
import os
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from core.config import get_settings
from core.orchestrator import run_research
from core.schemas import CompanyInput
from database.db import save_report

app = FastAPI(title="FinSight AI", version="1.0.0")

configured_origins = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173",
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in configured_origins if origin.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


class ResearchRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    symbol: str = Field(min_length=1, max_length=20)
    exchange: str = "NSE"
    days: int = Field(default=30, ge=7, le=365)


@app.get("/", response_class=HTMLResponse)
async def home() -> str:
    return PAGE


@app.get("/health")
async def health() -> dict[str, Any]:
    settings = get_settings()
    return {
        "status": "ok",
        "live_research_configured": bool(settings.tinyfish_api_key),
    }


@app.post("/api/research")
async def research(request: ResearchRequest) -> dict[str, Any]:
    try:
        company = CompanyInput(
            name=request.name.strip(),
            symbol=request.symbol.strip().upper(),
            exchange=request.exchange,
            research_period_days=request.days,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    report = await asyncio.to_thread(run_research, company)
    try:
        await asyncio.to_thread(save_report, report)
    except Exception as exc:
        report.errors.append(f"Report completed but could not be saved: {exc}")
    return report.model_dump(mode="json")


PAGE = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>FinSight AI · TinyFish intelligence</title>
  <style>
    :root{--ink:#f4f7fb;--muted:#9aa8ba;--bg:#08111f;--panel:#101d30;--line:#223550;--cyan:#55e0d0;--blue:#77a9ff;--red:#ff7f8e;--gold:#ffd27a}
    *{box-sizing:border-box}body{margin:0;color:var(--ink);background:radial-gradient(circle at 75% -10%,#173d55 0,#08111f 42%);font:15px/1.55 Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif}
    a{color:var(--cyan)}.shell{max-width:1180px;margin:auto;padding:28px 20px 70px}.nav{display:flex;justify-content:space-between;align-items:center;margin-bottom:75px}
    .brand{font-weight:800;letter-spacing:-.03em;font-size:20px}.brand span{color:var(--cyan)}.tinyfish{color:var(--muted);font-size:12px}.tinyfish b{color:var(--cyan)}
    .hero{max-width:780px}.eyebrow{color:var(--cyan);font-size:12px;font-weight:800;letter-spacing:.15em;text-transform:uppercase}.hero h1{font-size:clamp(42px,7vw,78px);line-height:.98;letter-spacing:-.07em;margin:15px 0 22px}.hero p{color:var(--muted);font-size:18px;max-width:670px}
    .card{background:rgba(16,29,48,.84);border:1px solid var(--line);border-radius:20px;box-shadow:0 20px 70px #0005}.form{display:grid;grid-template-columns:2fr 1fr 1fr auto;gap:12px;padding:14px;margin-top:35px}
    input,select,button{border:1px solid var(--line);border-radius:11px;background:#0b1728;color:var(--ink);padding:13px 14px;font:inherit}button{background:var(--cyan);color:#06151a;border:0;font-weight:800;cursor:pointer}button:disabled{opacity:.55;cursor:wait}
    .hint{color:var(--muted);font-size:12px;margin:12px 3px 0}.hidden{display:none}.loading{margin:35px 0;color:var(--cyan)}.result{margin-top:42px}
    .summary{display:grid;grid-template-columns:1.2fr 2fr 1fr;gap:1px;overflow:hidden}.summary>div{padding:24px;background:var(--panel)}.label{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.1em}.signal{font-size:38px;font-weight:850;margin-top:8px}.signal.BUY{color:var(--cyan)}.signal.SELL{color:var(--red)}.signal.HOLD{color:var(--gold)}.signal.WATCH{color:var(--blue)}
    .body-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:18px}.section{padding:24px}.section h2{margin:0 0 18px;font-size:20px}.item{border-top:1px solid var(--line);padding:15px 0}.item:first-of-type{border-top:0;padding-top:0}.item h3{margin:0 0 5px;font-size:15px}.item p{margin:0;color:var(--muted)}.meta{color:var(--muted);font-size:12px;margin-top:8px}.points{margin:0;padding-left:20px}.points li{margin:0 0 9px;color:#d9e4f2}.points li::marker{color:var(--cyan)}
    .metrics{display:grid;grid-template-columns:repeat(4, minmax(0, 1fr));gap:12px;margin:18px 0}.metric-card{background:#0e1a2b;border:1px solid var(--line);border-radius:14px;padding:14px}.metric-card .label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.1em}.metric-card .value{font-size:26px;font-weight:800;margin:8px 0}.metric-card .change{font-size:12px;color:var(--cyan)}
    .chart-shell{margin-top:12px;background:#08111f;border:1px solid var(--line);border-radius:12px;padding:12px}.chart-label{display:flex;justify-content:space-between;color:var(--muted);font-size:11px;margin-bottom:8px}.chart-bar{height:10px;border-radius:999px;background:linear-gradient(90deg,#55e0d0,#77a9ff);margin-bottom:10px}
    .chart-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px;margin:18px 0}.line-chart{width:100%;height:150px}.chart-axis{display:flex;justify-content:space-between;color:var(--muted);font-size:10px}.bar-row{display:grid;grid-template-columns:80px 1fr 70px;gap:8px;align-items:center;margin:10px 0;font-size:11px}.bar-track{height:12px;background:#1a2a40;border-radius:99px;overflow:hidden}.bar-fill{height:100%;background:linear-gradient(90deg,var(--cyan),var(--blue));border-radius:99px}
    .pill{display:inline-block;padding:3px 8px;border-radius:20px;background:#1a3150;color:var(--blue);font-size:11px}.notice{padding:13px 15px;border-radius:10px;background:#15332f;color:#b9fff0;margin-bottom:18px}.error{background:#3a202a;color:#ffc1c8}.footer{margin-top:52px;color:var(--muted);font-size:12px;text-align:center}
    @media(max-width:800px){.nav{margin-bottom:45px}.form,.summary,.body-grid{grid-template-columns:1fr}.form button{width:100%}}
  </style>
</head>
<body><main class="shell">
  <nav class="nav"><div class="brand">FinSight <span>AI</span></div><div class="tinyfish">Research infrastructure by <b>TinyFish</b> · evidence first</div></nav>
  <section class="hero"><div class="eyebrow">Market intelligence, without the noise</div><h1>See the signal behind the story.</h1><p>FinSight AI uses TinyFish browser agents to turn company news, disclosures, and history into a source-linked briefing.</p></section>
  <form class="card form" id="research-form"><input id="name" placeholder="Company name" value="Infosys Limited" required><input id="symbol" placeholder="Symbol" value="INFY" required><select id="exchange"><option>NSE</option><option>BSE</option></select><button id="submit">Run research</button></form>
  <div class="hint">TinyFish searches and fetches source pages in parallel. This is AI-generated research, not personalized investment advice.</div>
  <div id="loading" class="loading hidden">Running TinyFish research agents and financial synthesis…<br><span id="loading-detail">Searching trusted financial sources. This can take up to 90 seconds.</span></div><section id="result" class="result hidden"></section>
  <footer class="footer">Powered by <b>TinyFish</b> search and fetch · Built for transparent, source-linked research.</footer>
</main>
<script>
const $=id=>document.getElementById(id), esc=x=>String(x??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));
const points=items=>`<ul class="points">${(items||[]).map(x=>`<li>${esc(x)}</li>`).join("")}</ul>`;
const sentences=text=>String(text||"").split(/(?<=[.!?])\s+/).filter(Boolean).slice(0,3);
const metricCards=(items)=>`<div class="metrics">${(items||[]).slice(0,4).map(m=>`<div class="metric-card"><div class="label">${esc(m.label||"Metric")}</div><div class="value">${esc(m.value||"-")}</div>${m.change?`<div class="change">${esc(m.change)}</div>`:""}</div>`).join("")}</div>`;
function compactChart(items) {
  const values = (items || []).slice(0, 4);
  const rows = values.map((m, i) => {
    const width = Math.max(20, ((i + 1) / (values.length || 1)) * 100);
    return '<div><div class="chart-label"><span>' + esc(m.label || "Metric") +
      '</span><span>' + esc(m.value || "-") +
      '</span></div><div class="chart-bar" style="width:' + width + '%"></div></div>';
  }).join("");
  return '<div class="chart-shell"><div class="chart-label"><span>Key figures</span><span>' +
    values.length + ' metrics</span></div>' + rows + '</div>';
}
const seriesCharts=(series)=>`<div class="chart-grid">${(series||[]).slice(0,4).map(s=>{const p=s.points||[], max=Math.max(...p.map(x=>x.value),1), min=Math.min(...p.map(x=>x.value),0), range=max-min||1, coords=p.map((x,i)=>`${p.length===1?50:(i/(p.length-1))*100},${140-((x.value-min)/range)*115}`).join(" ");return `<div class="card section"><h2>${esc(s.metric)} <span class="meta">${esc(s.unit)}</span></h2>${p.length>1?`<svg class="line-chart" viewBox="0 0 100 150" preserveAspectRatio="none"><polyline points="${coords}" fill="none" stroke="#55e0d0" stroke-width="2" vector-effect="non-scaling-stroke"/></svg><div class="chart-axis">${esc(p[0].period)}<span>${esc(p[p.length-1].period)}</span></div>`:p.map(x=>`<div class="bar-row"><span>${esc(x.period)}</span><div class="bar-track"><div class="bar-fill" style="width:${Math.max(4,((x.value-min)/range)*100)}%"></div></div><span>${esc(x.value)}</span></div>`).join("")}</div>`}).join("")}</div>`;
const list=(title,items,mapper)=>`<div class="card section"><h2>${title}</h2>${items?.length?items.map(mapper).join(""):'<p class="meta">No sufficiently supported findings returned.</p>'}</div>`;
$("research-form").addEventListener("submit",async e=>{e.preventDefault();$("submit").disabled=true;$("loading").classList.remove("hidden");$("result").classList.add("hidden");const started=Date.now();const timer=setInterval(()=>{$("loading-detail").textContent="TinyFish is collecting sources and structuring the financial summary ("+Math.round((Date.now()-started)/1000)+"s elapsed).";},1000);
 try{const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),120000);const r=await fetch("/api/research",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:$("name").value,symbol:$("symbol").value,exchange:$("exchange").value,days:30}),signal:controller.signal});clearTimeout(timeout);const d=await r.json();if(!r.ok)throw Error(d.detail||"Research request failed");render(d)}
 catch(err){$("result").innerHTML=`<div class="card section notice error">${esc(err.name==="AbortError"?"Research timed out after 120 seconds. Check the backend logs and try again.":err.message)}</div>`;$("result").classList.remove("hidden")}finally{clearInterval(timer);$("submit").disabled=false;$("loading").classList.add("hidden")}}); 
function render(d){const a=d.analysis||{};const rawErrors=d.errors||[];const sourceFailures=rawErrors.filter(x=>x.startsWith("Could not fetch source:"));const notes=rawErrors.slice(0,5);const error=rawErrors.length?`<details class="notice error"><summary>${sourceFailures.length?`${sourceFailures.length} source${sourceFailures.length===1?"":"s"} unavailable`:"Research completed with notes"}</summary>${points(notes)}</details>`:"";const assessment=sentences(a.overall_assessment);$("result").innerHTML=`${error}<div class="card summary"><div><div class="label">Signal</div><div class="signal ${esc(a.signal)}">${esc(a.signal||"WATCH")}</div></div><div><div class="label">Assessment</div>${points(assessment.length?assessment:["Analysis unavailable."])}</div><div><div class="label">Confidence</div><p>${esc(a.confidence||"Low")}<br><span class="meta">${esc(d.duration_seconds)}s · ${d.news.findings.length+d.history.findings.length} sources</span></p></div></div>${metricCards(a.financial_metrics || [])}${seriesCharts(a.financial_series || [])}${compactChart(a.financial_metrics || [])}<div class="body-grid">${list("Key positives",a.bullish_factors.slice(0,5),x=>`<article class="item"><h3>${esc(x.factor)}</h3><p>${esc(x.evidence)}</p></article>`)}${list("Key risks",a.bearish_factors.slice(0,5),x=>`<article class="item"><h3>${esc(x.factor)}</h3><p>${esc(x.evidence)}</p></article>`)}${list("Recent intelligence",d.news.findings.slice(0,5),x=>`<article class="item"><h3>${esc(x.title)}</h3><p>${esc(x.summary)}</p><div class="meta"><span class="pill">${esc(x.sentiment)}</span> · ${esc(x.source||"Source unavailable")} · <a href="${esc(x.url)}" target="_blank" rel="noreferrer">Open source</a></div></article>`)}${list("Historical context",d.history.findings.slice(0,5),x=>`<article class="item"><h3>${esc(x.event)}</h3><p>${esc(x.description)}</p><div class="meta">${esc(x.date||"Date unavailable")} · <span class="pill">${esc(x.fact_status)}</span> · <a href="${esc(x.url)}" target="_blank" rel="noreferrer">Open source</a></div></article>`)}${list("What to watch next",(a.key_developments||[]).concat(a.major_risks||[]).slice(0,5),x=>`<article class="item"><p>${esc(x)}</p></article>`)}</div>`;$("result").classList.remove("hidden")}
</script></body></html>"""
