# ruff: noqa: E501
"""Local web app (`allocate serve`): editable detail views, charts, and goal tracking.

NOT FINANCIAL ADVICE. The server only reads/writes the local JSON store and computes
arithmetic from it. It binds to localhost, is single-user, keyless, and offline (Chart.js
is vendored locally). It does not call any model or external API.

`compute_view` and `validate_store` are Flask-free so they can be unit-tested without a
server; `create_app` imports Flask lazily so the rest of the package stays dependency-light.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from importlib.resources import files
from typing import Any

from asset_allocator import budget, goals
from asset_allocator.config import ASSET_CLASSES
from asset_allocator.i18n import _UI, bucket_emoji, bucket_label, category_emoji, normalize_lang, t
from asset_allocator.models import TargetAllocation
from asset_allocator.store import save
from asset_allocator.valuation import revalue

_KINDS = {"market", "accrual", "static"}
_MAX_ROWS = 500


def _target(data: dict[str, Any]) -> TargetAllocation:
    raw = data.get("target")
    if isinstance(raw, dict) and isinstance(raw.get("weights"), dict):
        return TargetAllocation(
            profile_name=str(raw.get("profile_name", "custom")), weights=raw["weights"]
        )
    return TargetAllocation(profile_name="none", weights={bucket: 0.0 for bucket in ASSET_CLASSES})


def compute_view(
    data: dict[str, Any],
    lang: str,
    ccy: str,
    as_of_year: int,
    *,
    assumed_return: float = 7.0,
) -> dict[str, Any]:
    """Build the computed bundle the page renders: status, budget, goals, charts."""
    lang = normalize_lang(lang)
    target = _target(data)
    status = revalue(
        data.get("holdings", []),
        target,
        as_of=f"{as_of_year:04d}-01-01T00:00:00+00:00",
        base_ccy=ccy,
        refresh=False,
        cache=data.get("price_cache", {}),
    )
    buckets = [
        {
            "bucket": b.bucket,
            "label": bucket_label(lang, b.bucket),
            "emoji": bucket_emoji(b.bucket),
            "value": b.market_value,
            "cost": b.cost_basis,
            "pnl": b.pnl,
            "pnl_pct": b.pnl_pct,
            "current": b.current_weight,
            "target": b.target_weight,
            "drift": b.drift,
        }
        for b in status.buckets
    ]

    income_items = budget.load_items(data, "income")
    expense_items = budget.load_items(data, "expense")
    has_budget = bool(income_items or expense_items)
    summary = budget.summarize(data)

    def _cf(item: Any) -> dict[str, Any]:
        return {
            "label": item.label,
            "category": item.category,
            "emoji": category_emoji(item.category or item.label),
            "amount": item.amount,
            "freq": item.freq,
            "monthly": round(budget.monthly_value(item), 2),
        }

    by_cat: dict[str, float] = {}
    for item in expense_items:
        key = item.category or "—"
        by_cat[key] = round(by_cat.get(key, 0.0) + budget.monthly_value(item), 2)
    expense_by_category = [
        {"category": cat, "emoji": category_emoji(cat), "monthly": amount}
        for cat, amount in sorted(by_cat.items(), key=lambda kv: kv[1], reverse=True)
    ]

    goal_items = goals.load_goals(data)
    goal_progress = [
        asdict(goals.goal_progress(g, status.total_value, as_of_year)) for g in goal_items
    ]

    last_year = max([g.year for g in goal_items] + [as_of_year + 10])
    years_n = max(1, last_year - as_of_year)
    monthly_contrib = summary.monthly_surplus if has_budget else 0.0
    traj_years = [as_of_year]
    traj_values = [round(status.total_value, 2)]
    balance = status.total_value
    monthly_rate = (1.0 + assumed_return / 100.0) ** (1.0 / 12.0) - 1.0
    for step in range(1, years_n + 1):
        for _ in range(12):
            balance = balance * (1.0 + monthly_rate) + monthly_contrib
        traj_years.append(as_of_year + step)
        traj_values.append(round(balance, 2))

    return {
        "ccy": ccy,
        "lang": lang,
        "as_of_year": as_of_year,
        "assumed_return": assumed_return,
        "net_worth": status.total_value,
        "total_cost": status.total_cost,
        "total_pnl": status.total_pnl,
        "total_pnl_pct": status.total_pnl_pct,
        "buckets": buckets,
        "has_budget": has_budget,
        "budget": asdict(summary),
        "income": [_cf(i) for i in income_items],
        "expense": [_cf(e) for e in expense_items],
        "expense_by_category": expense_by_category,
        "holdings": data.get("holdings", []),
        "goals": goal_progress,
        "goals_raw": [asdict(g) for g in goal_items],
        "trajectory": {
            "years": traj_years,
            "projected": traj_values,
            "goals": [{"year": g.year, "label": g.label, "target": g.target} for g in goal_items],
        },
    }


def validate_store(data: dict[str, Any]) -> None:
    """Validate the editable parts of a posted store; raise ValueError on the first problem."""
    if not isinstance(data, dict):
        raise ValueError("Payload must be a JSON object.")
    holdings = data.get("holdings", [])
    cashflow = data.get("cashflow", [])
    goal_rows = data.get("goals", [])
    for name, rows in (("holdings", holdings), ("cashflow", cashflow), ("goals", goal_rows)):
        if not isinstance(rows, list):
            raise ValueError(f"'{name}' must be a list.")
        if len(rows) > _MAX_ROWS:
            raise ValueError(f"Too many '{name}' rows (max {_MAX_ROWS}).")
    for row in holdings:
        if not isinstance(row, dict):
            raise ValueError("Each holding must be an object.")
        if row.get("bucket") not in ASSET_CLASSES:
            raise ValueError(f"Holding has invalid bucket: {row.get('bucket')!r}.")
        if not str(row.get("label", "")).strip():
            raise ValueError("Each holding needs a label.")
        if row.get("kind") not in _KINDS:
            raise ValueError(f"Holding {row.get('label')!r} has invalid kind {row.get('kind')!r}.")
        try:
            float(row.get("cost_basis", 0))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Holding {row.get('label')!r} cost_basis must be a number.") from exc
    for row in cashflow:
        if not isinstance(row, dict):
            raise ValueError("Each cash-flow item must be an object.")
        if row.get("kind") not in ("income", "expense"):
            raise ValueError(f"Cash-flow kind must be income/expense, got {row.get('kind')!r}.")
        if row.get("freq") not in ("monthly", "yearly"):
            raise ValueError(f"Cash-flow freq must be monthly/yearly, got {row.get('freq')!r}.")
        if not str(row.get("label", "")).strip():
            raise ValueError("Each cash-flow item needs a label.")
        try:
            if float(row.get("amount", 0)) < 0:
                raise ValueError("Cash-flow amount must be non-negative.")
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Cash-flow {row.get('label')!r} amount must be a number.") from exc
    for row in goal_rows:
        if not isinstance(row, dict):
            raise ValueError("Each goal must be an object.")
        if not str(row.get("label", "")).strip():
            raise ValueError("Each goal needs a label.")
        try:
            if int(row.get("year", 0)) < 1900:
                raise ValueError("Goal year looks invalid.")
            if float(row.get("target", 0)) <= 0:
                raise ValueError("Goal target must be positive.")
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Goal {row.get('label')!r} has invalid year/target.") from exc


def chartjs_source() -> str:
    """Return the vendored Chart.js UMD source (offline, no CDN)."""
    return (
        files("asset_allocator").joinpath("web_assets/chart.umd.min.js").read_text(encoding="utf-8")
    )


def render_page(data: dict[str, Any], lang: str, ccy: str, as_of_year: int) -> str:
    lang = normalize_lang(lang)
    state = compute_view(data, lang, ccy, as_of_year)
    tmap = {key: t(lang, key) for key in _UI["en"]}
    return (
        _PAGE.replace("__STATE__", json.dumps(state, ensure_ascii=False))
        .replace("__T__", json.dumps(tmap, ensure_ascii=False))
        .replace("__LANG__", lang)
        .replace("__CCY__", ccy)
        .replace("__TITLE__", t(lang, "title"))
    )


def create_app(
    store_path: str, *, lang: str = "en", currency: str = "VND", as_of_year: int = 2026
) -> Any:
    from flask import Flask, Response, jsonify, request

    from asset_allocator.store import load

    app = Flask(__name__)
    lang_n = normalize_lang(lang)

    def _load() -> dict[str, Any]:
        try:
            return load(store_path)
        except Exception:
            return {
                "profile": None,
                "target": None,
                "holdings": [],
                "price_cache": {},
                "history": [],
                "cashflow": [],
                "goals": [],
            }

    @app.get("/")
    def index() -> Any:
        return Response(render_page(_load(), lang_n, currency, as_of_year), mimetype="text/html")

    @app.get("/api/state")
    def state() -> Any:
        data = _load()
        return jsonify({"data": data, "view": compute_view(data, lang_n, currency, as_of_year)})

    @app.post("/api/save")
    def save_route() -> Any:
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({"ok": False, "error": "Invalid JSON body."}), 400
        try:
            validate_store(payload)
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        current = _load()
        for key in ("holdings", "cashflow", "goals", "target"):
            if key in payload:
                current[key] = payload[key]
        save(current, store_path)
        return jsonify({"ok": True, "view": compute_view(current, lang_n, currency, as_of_year)})

    @app.get("/vendor/chart.js")
    def chart_js() -> Any:
        return Response(chartjs_source(), mimetype="application/javascript")

    return app


_PAGE = r"""<!doctype html>
<html lang="__LANG__">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<script src="/vendor/chart.js"></script>
<style>
:root{--bg:#f1f5f9;--panel:#fff;--ink:#0f172a;--muted:#64748b;--line:#e2e8f0;--accent:#4f46e5;--up:#16a34a;--down:#dc2626;}
*{box-sizing:border-box;}
body{font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;margin:0;color:var(--ink);background:var(--bg);}
.bar-top{height:5px;background:linear-gradient(90deg,#4f46e5,#06b6d4,#16a34a);}
main{max-width:1140px;margin:0 auto;padding:24px 18px 64px;}
header{display:flex;justify-content:space-between;align-items:flex-end;gap:12px;flex-wrap:wrap;}
h1{margin:0;font-size:24px;letter-spacing:-.02em;}
.sub{color:var(--muted);font-size:13px;margin-top:3px;}
.unit{color:var(--muted);font-size:12px;text-align:right;}
.toolbar{display:flex;gap:8px;align-items:center;margin:16px 0;flex-wrap:wrap;}
button{font:inherit;border:1px solid var(--line);background:#fff;border-radius:9px;padding:8px 14px;cursor:pointer;}
button.primary{background:var(--accent);color:#fff;border-color:var(--accent);font-weight:600;}
button.mini{padding:3px 9px;border-radius:7px;font-size:13px;}
#toast{position:fixed;right:18px;bottom:18px;background:#0f172a;color:#fff;padding:10px 16px;border-radius:10px;opacity:0;transition:.3s;pointer-events:none;}
#toast.show{opacity:1;}
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:8px 0 20px;}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px 16px;box-shadow:0 1px 2px rgba(15,23,42,.04);}
.card-k{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.04em;}
.card-v{font-size:21px;font-weight:700;margin-top:5px;font-variant-numeric:tabular-nums;}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px;box-shadow:0 1px 2px rgba(15,23,42,.04);margin-bottom:18px;}
h2{font-size:16px;margin:0 0 14px;}
.charts{display:grid;grid-template-columns:repeat(2,1fr);gap:18px;}
.chartbox{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px;}
.chartbox h2{font-size:14px;}
.chartwrap{position:relative;height:260px;}
table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;font-size:14px;}
th,td{padding:7px 8px;border-bottom:1px solid var(--line);text-align:right;}
th:first-child,td:first-child,th:nth-child(2),td:nth-child(2){text-align:left;}
th{color:var(--muted);font-size:12px;font-weight:600;text-transform:uppercase;}
input,select{font:inherit;border:1px solid var(--line);border-radius:7px;padding:5px 7px;width:100%;background:#fff;}
input[type=number]{text-align:right;}
.up{color:var(--up);}.down{color:var(--down);}.flat{color:var(--muted);}
.goal{display:grid;grid-template-columns:1fr;gap:6px;padding:12px 0;border-bottom:1px solid var(--line);}
.goal-bar{height:10px;background:#eef2f7;border-radius:6px;overflow:hidden;}
.goal-bar i{display:block;height:10px;background:linear-gradient(90deg,#4f46e5,#16a34a);}
.goal-meta{display:flex;justify-content:space-between;gap:10px;font-size:13px;color:var(--muted);flex-wrap:wrap;}
.disclaimer{margin-top:18px;padding:11px 15px;background:#fff7ed;border:1px solid #fed7aa;border-radius:10px;color:#9a3412;font-size:13px;}
@media(max-width:860px){.cards{grid-template-columns:repeat(2,1fr);}.charts{grid-template-columns:1fr;}}
</style>
</head>
<body>
<div class="bar-top"></div>
<main>
<header>
<div><h1 id="title"></h1><div class="sub" id="subtitle"></div></div>
<div class="unit" id="unitnote"></div>
</header>
<div class="toolbar">
<button class="primary" id="saveBtn"></button>
<span id="status" class="sub"></span>
</div>
<section class="cards" id="kpis"></section>
<section class="panel" id="goalsPanel"></section>
<section class="charts" id="charts"></section>
<section class="panel"><h2 id="incomeTitle"></h2><div id="incomeTable"></div><button class="mini" data-add="income"></button></section>
<section class="panel"><h2 id="expenseTitle"></h2><div id="expenseTable"></div><button class="mini" data-add="expense"></button></section>
<section class="panel"><h2 id="holdingsTitle"></h2><div id="holdingsTable"></div><button class="mini" data-add="holding"></button></section>
<p class="disclaimer" id="disclaimer"></p>
</main>
<div id="toast"></div>
<script>
const T=__T__, LANG="__LANG__", CCY="__CCY__";
let STATE=__STATE__;
let DATA=null;
const BUCKETS=["equity","bonds","gold","real_estate","savings","cash","emergency"];
const charts={};
function fmt(n){const neg=n<0;n=Math.abs(Math.round((n+Number.EPSILON)*100)/100);let s=n.toLocaleString(LANG==="vi"?"de-DE":"en-US",{maximumFractionDigits:2});return (neg?"-":"")+s;}
function el(t,a={},...kids){const e=document.createElement(t);for(const k in a){if(k==="class")e.className=a[k];else if(k==="html")e.innerHTML=a[k];else e.setAttribute(k,a[k]);}for(const c of kids)e.append(c.nodeType?c:document.createTextNode(c));return e;}
function cls(n){return n>0?"up":n<0?"down":"flat";}
function toast(msg,ok=true){const x=document.getElementById("toast");x.textContent=msg;x.style.background=ok?"#0f172a":"#b91c1c";x.classList.add("show");setTimeout(()=>x.classList.remove("show"),2200);}

async function boot(){const r=await fetch("/api/state");const j=await r.json();STATE=j.view;DATA=j.data;render();}
function labels(){document.title=T.title;document.getElementById("title").textContent=T.title;document.getElementById("subtitle").textContent=T.subtitle;document.getElementById("unitnote").textContent=T.unit_note+": "+CCY;document.getElementById("saveBtn").textContent="💾 "+T.save;document.getElementById("incomeTitle").textContent="💵 "+T.detail_income;document.getElementById("expenseTitle").textContent="🧾 "+T.detail_expense;document.getElementById("holdingsTitle").textContent="🏦 "+T.detail_holdings;document.getElementById("disclaimer").textContent=T.disclaimer;document.querySelector('[data-add=income]').textContent="+ "+T.add;document.querySelector('[data-add=expense]').textContent="+ "+T.add;document.querySelector('[data-add=holding]').textContent="+ "+T.add;}

function kpis(){const v=STATE;const cards=[[T.net_worth,fmt(v.net_worth),""],[T.total_pnl,fmt(v.total_pnl)+" ("+(v.total_pnl_pct>0?"+":"")+v.total_pnl_pct.toFixed(2)+"%)",cls(v.total_pnl)],[T.surplus_mo,v.has_budget?fmt(v.budget.monthly_surplus):"–",v.has_budget?cls(v.budget.monthly_surplus):""],[T.savings_rate,v.has_budget?v.budget.savings_rate.toFixed(1)+"%":"–",""]];const box=document.getElementById("kpis");box.innerHTML="";for(const[k,val,c]of cards)box.append(el("div",{class:"card"},el("div",{class:"card-k"},k),el("div",{class:"card-v "+(c||"")},val)));}

function goalsPanel(){const p=document.getElementById("goalsPanel");p.innerHTML="";if(!STATE.goals.length){p.style.display="none";return;}p.style.display="";p.append(el("h2",{},"🎯 "+T.goal_progress));for(const g of STATE.goals){const pct=Math.max(0,Math.min(100,g.progress_pct));const bar=el("div",{class:"goal-bar"},el("i",{style:"width:"+pct+"%"}));const meta=el("div",{class:"goal-meta"},el("span",{},g.year+" · "+g.label),el("span",{},T.target_nw+": "+fmt(g.target)),el("span",{},T.gap+": "+fmt(g.gap)),el("span",{},T.years_left+": "+g.years_left),el("span",{},T.required_return+": "+g.required_cagr.toFixed(1)+"%"));p.append(el("div",{class:"goal"},el("div",{class:"goal-meta"},el("strong",{},g.progress_pct.toFixed(1)+"%")),bar,meta));}}

function chartBox(id,title){const b=el("div",{class:"chartbox"},el("h2",{},title),el("div",{class:"chartwrap"},el("canvas",{id:id})));document.getElementById("charts").append(b);return id;}
function mk(id,cfg){if(charts[id])charts[id].destroy();charts[id]=new Chart(document.getElementById(id),cfg);}
const PAL=["#4f46e5","#16a34a","#d97706","#7c3aed","#0891b2","#dc2626","#64748b","#db2777","#0d9488","#ca8a04"];
function charts_render(){document.getElementById("charts").innerHTML="";const v=STATE;
 if(v.expense_by_category.length){chartBox("cExp",T.chart_expense_cat);mk("cExp",{type:"doughnut",data:{labels:v.expense_by_category.map(e=>e.emoji+" "+e.category),datasets:[{data:v.expense_by_category.map(e=>e.monthly),backgroundColor:PAL}]},options:{plugins:{legend:{position:"right"}},responsive:true,maintainAspectRatio:false}});}
 if(v.has_budget){chartBox("cIE",T.chart_income_expense);mk("cIE",{type:"bar",data:{labels:[T.income_mo,T.expense_mo,T.surplus_mo],datasets:[{data:[v.budget.monthly_income,v.budget.monthly_expense,v.budget.monthly_surplus],backgroundColor:["#16a34a","#dc2626","#4f46e5"]}]},options:{plugins:{legend:{display:false}},responsive:true,maintainAspectRatio:false}});
 const sr=Math.max(0,Math.min(100,v.budget.savings_rate));chartBox("cSav",T.chart_savings);mk("cSav",{type:"doughnut",data:{labels:[T.savings_rate,""],datasets:[{data:[sr,100-sr],backgroundColor:["#16a34a","#e2e8f0"]}]},options:{circumference:180,rotation:270,cutout:"70%",plugins:{legend:{display:false},tooltip:{enabled:false}},responsive:true,maintainAspectRatio:false}});}
 const tr=v.trajectory;const ds=[{label:T.projected,data:tr.years.map((y,i)=>({x:y,y:tr.projected[i]})),borderColor:"#4f46e5",backgroundColor:"#4f46e5",tension:.2}];if(tr.goals.length)ds.push({label:T.goals,data:tr.goals.map(g=>({x:g.year,y:g.target})),borderColor:"#dc2626",backgroundColor:"#dc2626",showLine:false,pointRadius:6,pointStyle:"star"});chartBox("cGoal",tr.goals.length?T.chart_goals:T.chart_history);mk("cGoal",{type:"line",data:{datasets:ds},options:{parsing:false,scales:{x:{type:"linear",ticks:{precision:0}}},responsive:true,maintainAspectRatio:false}});}

function row(cells){const tr=el("tr");for(const c of cells)tr.append(el("td",{},c));return tr;}
function inp(val,type="text"){return el("input",type==="number"?{type:"number",step:"any",value:val}:{value:val});}
function delBtn(fn){const b=el("button",{class:"mini"},"✕");b.onclick=fn;return b;}
function tableHead(cols){const t=el("tr");for(const c of cols)t.append(el("th",{},c));return t;}

function cfTable(divId,kind){const div=document.getElementById(divId);div.innerHTML="";const items=DATA.cashflow.filter(x=>x.kind===kind);const tb=el("table");const thead=el("thead",{},tableHead(["",T.label,T.category,T.amount,T.freq,""]));const body=el("tbody");items.forEach((it)=>{const tr=el("tr");const emo=el("td",{},(window.__catemo?window.__catemo(it.category||it.label):"")||"·");const li=inp(it.label||"");li.oninput=e=>it.label=e.target.value;const ci=inp(it.category||"");ci.oninput=e=>it.category=e.target.value;const ai=inp(it.amount||0,"number");ai.oninput=e=>it.amount=parseFloat(e.target.value)||0;const fs=el("select");["monthly","yearly"].forEach(f=>{const o=el("option",{value:f},T[f]||f);if(it.freq===f)o.selected=true;fs.append(o);});fs.onchange=e=>it.freq=e.target.value;const d=delBtn(()=>{DATA.cashflow.splice(DATA.cashflow.indexOf(it),1);cfTable(divId,kind);});[emo,el("td",{},li),el("td",{},ci),el("td",{},ai),el("td",{},fs),el("td",{},d)].forEach(td=>tr.append(td.nodeName?td:el("td",{},td)));body.append(tr);});tb.append(thead,body);div.append(tb);}

function holdingsTable(){const div=document.getElementById("holdingsTable");div.innerHTML="";const tb=el("table");const thead=el("thead",{},tableHead(["",T.label,T.col_bucket,T.kind,T.col_cost,""]));const body=el("tbody");DATA.holdings.forEach((h)=>{const tr=el("tr");const bsel=el("select");BUCKETS.forEach(b=>{const o=el("option",{value:b},b);if(h.bucket===b)o.selected=true;bsel.append(o);});bsel.onchange=e=>h.bucket=e.target.value;const ksel=el("select");["market","accrual","static"].forEach(k=>{const o=el("option",{value:k},k);if(h.kind===k)o.selected=true;ksel.append(o);});ksel.onchange=e=>h.kind=e.target.value;const li=inp(h.label||"");li.oninput=e=>h.label=e.target.value;const ci=inp(h.cost_basis||0,"number");ci.oninput=e=>h.cost_basis=parseFloat(e.target.value)||0;const d=delBtn(()=>{DATA.holdings.splice(DATA.holdings.indexOf(h),1);holdingsTable();});tr.append(el("td",{},"·"),el("td",{},li),el("td",{},bsel),el("td",{},ksel),el("td",{},ci),el("td",{},d));body.append(tr);});tb.append(thead,body);div.append(tb);}

function render(){labels();kpis();goalsPanel();charts_render();cfTable("incomeTable","income");cfTable("expenseTable","expense");holdingsTable();}
document.querySelector('[data-add=income]').onclick=()=>{DATA.cashflow.push({kind:"income",label:"",amount:0,freq:"monthly",category:""});cfTable("incomeTable","income");};
document.querySelector('[data-add=expense]').onclick=()=>{DATA.cashflow.push({kind:"expense",label:"",amount:0,freq:"monthly",category:""});cfTable("expenseTable","expense");};
document.querySelector('[data-add=holding]').onclick=()=>{DATA.holdings.push({bucket:"cash",label:"",kind:"static",cost_basis:0});holdingsTable();};
document.getElementById("saveBtn").onclick=async()=>{try{const r=await fetch("/api/save",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({holdings:DATA.holdings,cashflow:DATA.cashflow,goals:DATA.goals,target:DATA.target})});const j=await r.json();if(j.ok){STATE=j.view;kpis();goalsPanel();charts_render();toast("✓ "+T.saved);}else{toast(T.save_failed+": "+j.error,false);}}catch(e){toast(T.save_failed+": "+e,false);}};
boot();
</script>
</body>
</html>
"""
