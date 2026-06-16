"""
build.py — reads data.csv and writes index.html
Run manually:  python build.py
Or triggered automatically by GitHub Actions on every CSV upload.
"""

import json, re, math, pandas as pd
from pathlib import Path

# ── Country group definitions ─────────────────────────────────────────────────
G7  = {'Canada','France','Germany','Italy','Japan','United Kingdom','United States'}
G20 = {'Argentina','Australia','Brazil','Canada','China','France','Germany','India',
       'Indonesia','Italy','Japan','Korea, Rep.','Mexico','Russia','Saudi Arabia',
       'South Africa','Turkey','United Kingdom','United States','European Union'}
GCC = {'Bahrain','Kuwait','Oman','Qatar','Saudi Arabia','United Arab Emirates'}

# ── Category → indicator mapping ─────────────────────────────────────────────
CATS = {
    "🏛️ Political Representation": [
        "Women in parliament %","Seats held by women in national parliament (%)",
        "Seats Held By Women In National Parliament (%)","Women in ministerial positions %",
        "Years with female/male head of state (last 50)","Share of seats in parliament",
        "Females in parliament"
    ],
    "💼 Economic & Workforce": [
        "Economic Empowerment Of Women","Gender Earnings Gap","Gender Development Gap",
        "Business Opportunities For Women","Gender Parity In High-Skilled Jobs",
        "Gender parity in high-skilled jobs","Leadership opportunities for women",
        "Leadership Opportunities For Women","Can a woman get a job in the same way as a man?",
        "Can a woman work at night in the same way as a man?",
        "Can a woman work in a job deemed dangerous in the same way as a man?",
        "Can a woman work in an industrial job in the same way as a man?",
        "Does the law prohibit discrimination in employment based on gender?",
        "Does the law mandate equal remuneration for work of equal value?",
        "Protection Of Women'S Workplace, Education And Family Rights",
        "Gender inequality","Women on boards"
    ],
    "⚖️ Legal Rights & Freedom": [
        "Physical Security Of Women","Women'S Agency",
        "Is there legislation on sexual harassment in employment?",
        "Are there criminal penalties or civil remedies for sexual harassment in employment?",
        "Is there legislation specifically addressing domestic violence?",
        "Is the law free of legal provisions that require a married woman to obey her husband?",
        "Can a woman choose where to live in the same way as a man?",
        "Can a woman travel outside her home in the same way as a man?",
        "Can a woman travel outside the country in the same way as a man?",
        "Can a woman apply for a passport in the same way as a man?",
        "Can a woman be head of household in the same way as a man?",
        "Can a woman obtain a judgment of divorce in the same way as a man?",
        "Does a woman have the same rights to remarry as a man?"
    ],
    "💰 Financial & Business Rights": [
        "Can a woman open a bank account in the same way as a man?",
        "Can a woman sign a contract in the same way as a man?",
        "Can a woman register a business in the same way as a man?",
        "Does the law prohibit discrimination in access to credit based on gender?",
        "Do men and women have equal ownership rights to immovable property?",
        "Does the law grant spouses equal administrative authority over assets during marriage?",
        "Does the law provide for the valuation of nonmonetary contributions?",
        "Do male and female surviving spouses have equal rights to inherit assets?",
        "Do sons and daughters have equal rights to inherit assets from their parents?"
    ],
    "👶 Family, Maternity & Pension": [
        "Is paid leave of at least 14 weeks available to mothers?",
        "Is there paid leave available to fathers?","Is there paid parental leave?",
        "Is dismissal of pregnant workers prohibited?",
        "Does the government administer 100% of maternity leave benefits?",
        "Are periods of absence due to childcare accounted for in pension benefits?",
        "Is the age at which men and women can retire with full pension benefits the same?",
        "Is the age at which men and women can retire with partial pension benefits the same?",
        "Is the mandatory retirement age for men and women the same?"
    ],
    "📚 Education, Health & Technology": [
        "Equal Access To Quality Education (0=Unequal; 4=Equal)",
        "Equal Access To Quality Healthcare (0=Unequal; 4=Equal)",
        "Inequality in education 0-100 (highly unequal)",
        "Gender parity in internet usage","Gender parity in R&D","Gender statistics"
    ]
}

# ── Load CSV ──────────────────────────────────────────────────────────────────
print("Reading data.csv ...")
df = pd.read_csv("data.csv", low_memory=False)
print(f"  {len(df):,} rows loaded")

# ── UAE latest rows ───────────────────────────────────────────────────────────
uae_latest = df[(df["Country Name"] == "United Arab Emirates") & (df["Latest"] == "Latest")].copy()
print(f"  {len(uae_latest)} UAE latest indicators found")

# ── Helpers ───────────────────────────────────────────────────────────────────
def to_float(v):
    try:
        f = float(v)
        return None if math.isnan(f) else f
    except:
        return None

def grp_avg(peers, countries):
    vals = [to_float(v) for v in peers[peers["Country Name"].isin(countries)]["Score"]]
    vals = [v for v in vals if v is not None]
    return round(sum(vals) / len(vals), 4) if vals else None

def rank_diff(rank, prev):
    try:
        r, p = int(rank), int(prev)
        d = p - r
        if d > 0:  return f"▲{d}"
        if d < 0:  return f"▼{abs(d)}"
        return "►0"
    except:
        return "-"

def clean(v):
    s = str(v).strip()
    return "-" if s in ("nan", "", "Not Available") else s

# ── Build DATA object ─────────────────────────────────────────────────────────
bar_data   = {}
trend_data = {}

for _, urow in uae_latest.iterrows():
    report = urow["Report"]
    ind    = urow["Indicator (English)"]
    year   = int(urow["Year of Report"])

    peers = df[
        (df["Report"] == report) &
        (df["Indicator (English)"] == ind) &
        (df["Year of Report"] == year)
    ]

    world_vals = [to_float(v) for v in peers["Score"]]
    world_vals = [v for v in world_vals if v is not None]
    world_avg  = round(sum(world_vals) / len(world_vals), 4) if world_vals else None

    bar_data.setdefault(report, {})[ind] = {
        "latest_year": year,
        "UAE":         to_float(urow["Score"]),
        "G7_avg":      grp_avg(peers, G7),
        "G20_avg":     grp_avg(peers, G20),
        "GCC_avg":     grp_avg(peers, GCC),
        "World_avg":   world_avg,
        "rank":        clean(urow["Rank"]),
        "prev_rank":   clean(urow["Previous Rank"]),
        "rank_diff":   rank_diff(urow["Rank"], urow["Previous Rank"]),
        "first_global": clean(urow["First Globally"]),
        "first_arab":   clean(urow["First Arab"]),
        "first_gcc":    clean(urow["First GCC"]),
        "first_g20":    clean(urow["First G20"]),
        "description":  clean(urow["Indicator Description"]),
        "entity":       clean(urow["Main Entity (English)"]),
    }

    # Trend: all UAE rows for this report + indicator
    uae_hist = df[
        (df["Country Name"] == "United Arab Emirates") &
        (df["Report"] == report) &
        (df["Indicator (English)"] == ind)
    ].sort_values("Year of Report")

    pts = []
    for _, tr in uae_hist.iterrows():
        v = to_float(tr["Score"])
        if v is not None:
            pts.append({"year": int(tr["Year of Report"]), "score": v})

    if pts:
        trend_data.setdefault(report, {})[ind] = pts

# ── Report country counts ─────────────────────────────────────────────────────
report_countries = {
    rep: int(df[df["Report"] == rep]["Country Name"].nunique())
    for rep in bar_data
}

DATA = {"bar_data": bar_data, "trend_data": trend_data}

total_inds = sum(len(v) for v in bar_data.values())
print(f"  {len(bar_data)} reports, {total_inds} indicators processed")

# ── Inline JSON safely (no NaN) ───────────────────────────────────────────────
DATA_JS   = json.dumps(DATA)
RC_JS     = json.dumps(report_countries)
CATS_JS   = json.dumps(CATS, ensure_ascii=False)

# ── HTML template ─────────────────────────────────────────────────────────────
HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UAE Gender Balance Dashboard</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
:root{{
  --bg:#f5f7fa;--surface:#fff;--surface2:#f0f4f9;--border:#dde4ef;
  --b1:#0d3b8e;--b2:#1a5fbc;--b3:#2e80d4;--b4:#5aa8e8;--b5:#9ccbf4;
  --text:#1a2340;--muted:#7a8aaa;--green:#15803d;--red:#c0392b;
  --font:'Sakkal Majalla','Calibri','Trebuchet MS',sans-serif;
}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:var(--bg);color:var(--text);font-family:var(--font);min-height:100vh}}
.hdr{{background:linear-gradient(135deg,#0a2560,#0d3b8e 55%,#1a5fbc);padding:22px 36px;display:flex;align-items:center;gap:14px;position:relative;overflow:hidden;box-shadow:0 4px 24px rgba(13,59,142,.2)}}
.hdr::before{{content:'';position:absolute;bottom:0;left:0;right:0;height:3px;background:linear-gradient(90deg,#00843D,#fff 50%,#ef4135)}}
.hdr::after{{content:'';position:absolute;top:-60px;right:-60px;width:360px;height:360px;background:radial-gradient(circle,rgba(255,255,255,.07),transparent 60%);pointer-events:none}}
.flag{{display:flex;gap:3px;flex-shrink:0}}
.flag .r{{width:6px;height:44px;background:#ef4135;border-radius:3px}}
.flag .s{{display:flex;flex-direction:column;width:6px;height:44px;border-radius:3px;overflow:hidden}}
.flag .s div{{flex:1}}
.flag .s .g{{background:#00843D}}.flag .s .w{{background:#fff}}.flag .s .b{{background:#111}}
.hdr-txt{{margin-left:6px;flex:1}}
.hdr-txt h1{{font-size:26px;font-weight:800;color:#fff;letter-spacing:-.3px}}
.hdr-txt p{{font-size:14px;color:rgba(255,255,255,.6);margin-top:3px}}
.hdr-badge{{margin-left:auto;background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);color:#fff;font-size:12px;font-weight:700;padding:6px 16px;border-radius:20px;letter-spacing:.8px;text-transform:uppercase;flex-shrink:0}}
.tabs-bar{{background:var(--surface);border-bottom:2px solid var(--border)}}
.tabs{{display:flex;padding:0 36px}}
.tab{{padding:16px 28px;font-size:16px;font-weight:600;color:var(--muted);cursor:pointer;border-bottom:3px solid transparent;margin-bottom:-2px;transition:color .2s,border-color .2s;user-select:none}}
.tab:hover{{color:var(--b1)}}.tab.active{{color:var(--b1);border-bottom-color:var(--b1)}}
.panel{{display:none}}.panel.active{{display:block}}
.pills{{display:flex;gap:16px;padding:22px 36px 0;flex-wrap:wrap}}
.pill{{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:16px 22px;display:flex;align-items:center;gap:14px;box-shadow:0 2px 10px rgba(13,59,142,.07);transition:box-shadow .2s,transform .2s}}
.pill:hover{{box-shadow:0 6px 20px rgba(13,59,142,.12);transform:translateY(-2px)}}
.pill-icon{{width:52px;height:52px;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:24px;flex-shrink:0}}
.pi-b{{background:linear-gradient(135deg,#dbeafe,#bfdbfe)}}.pi-t{{background:linear-gradient(135deg,#e0f2fe,#bae6fd)}}.pi-y{{background:linear-gradient(135deg,#fef9c3,#fde68a)}}
.pill-num{{font-size:34px;font-weight:800;color:var(--b1);line-height:1}}
.pill-lbl{{font-size:12px;font-weight:700;color:var(--muted);letter-spacing:.5px;text-transform:uppercase;margin-top:3px}}
.filter-section{{background:var(--surface);border:1px solid var(--border);border-radius:16px;margin:18px 36px 0;padding:20px 24px;box-shadow:0 2px 8px rgba(13,59,142,.05)}}
.mode-toggle{{display:flex;gap:0;margin-bottom:18px;background:var(--surface2);border-radius:10px;padding:4px;width:fit-content;border:1px solid var(--border)}}
.mode-btn{{padding:9px 22px;font-size:14px;font-weight:600;border-radius:8px;cursor:pointer;border:none;background:transparent;color:var(--muted);font-family:var(--font);transition:all .2s;user-select:none}}
.mode-btn.active{{background:var(--b1);color:#fff;box-shadow:0 2px 8px rgba(13,59,142,.3)}}
.mode-label{{font-size:11px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;color:var(--muted);margin-bottom:7px}}
.filter-row{{display:flex;gap:16px;flex-wrap:wrap;align-items:flex-end}}
.fg{{display:flex;flex-direction:column;gap:7px;flex:1;min-width:200px}}
.fg select{{background:var(--surface2);border:1.5px solid var(--border);color:var(--text);padding:11px 36px 11px 14px;border-radius:9px;font-family:var(--font);font-size:15px;font-weight:500;cursor:pointer;outline:none;appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%237a8aaa' d='M6 8L1 3h10z'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 12px center;transition:border-color .2s,box-shadow .2s}}
.fg select:focus{{border-color:var(--b1);box-shadow:0 0 0 3px rgba(13,59,142,.1)}}
.mode-panel{{display:none}}.mode-panel.active{{display:block}}
.cat-indicator-count{{font-size:13px;color:var(--muted);margin-top:10px;padding-top:10px;border-top:1px solid var(--border)}}
.cat-indicator-count span{{font-weight:700;color:var(--b1)}}
.kpi-row{{display:flex;gap:14px;padding:16px 36px 0;flex-wrap:wrap}}
.kpi{{background:var(--surface);border:1px solid var(--border);border-radius:13px;padding:18px 20px;flex:1;min-width:130px;position:relative;overflow:hidden;box-shadow:0 2px 8px rgba(13,59,142,.05);transition:box-shadow .2s,transform .2s}}
.kpi:hover{{box-shadow:0 5px 18px rgba(13,59,142,.1);transform:translateY(-1px)}}
.kpi::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px;border-radius:13px 13px 0 0}}
.kpi.c1::before{{background:var(--b1)}}.kpi.c2::before{{background:var(--b2)}}.kpi.c3::before{{background:var(--b3)}}.kpi.c4::before{{background:var(--b4)}}.kpi.c5::before{{background:var(--b5)}}.kpi.c6::before{{background:#7c3aed}}.kpi.c7::before{{background:#0369a1}}.kpi.c8::before{{background:#0f766e}}
.kpi-lbl{{font-size:11px;font-weight:700;letter-spacing:.7px;text-transform:uppercase;color:var(--muted);margin-bottom:9px}}
.kpi-val{{font-size:30px;font-weight:800;line-height:1}}
.kpi.c1 .kpi-val{{color:var(--b1)}}.kpi.c2 .kpi-val{{color:var(--b2)}}.kpi.c3 .kpi-val{{color:var(--b3)}}.kpi.c4 .kpi-val{{color:var(--b4)}}.kpi.c5 .kpi-val{{color:#3a8fd4}}.kpi.c6 .kpi-val{{color:#7c3aed}}.kpi.c7 .kpi-val{{color:#0369a1}}.kpi.c8 .kpi-val{{color:#0f766e;font-size:15px;font-weight:700;line-height:1.3;margin-top:4px;word-break:break-word}}
.kpi-meta{{font-size:12px;color:var(--muted);margin-top:5px}}
.kpi-diff{{font-size:12px;font-weight:600;margin-top:4px}}
.kpi-diff.pos{{color:var(--green)}}.kpi-diff.neg{{color:var(--red)}}.kpi-diff.neu{{color:var(--muted)}}
.rank-row{{display:flex;align-items:baseline;gap:5px;margin-top:4px}}
.rank-num{{font-size:28px;font-weight:800;color:#7c3aed}}
.rank-of{{font-size:13px;color:var(--muted);font-weight:600}}
.rank-arrow{{font-size:13px;font-weight:700;display:block;margin-top:3px}}
.rank-arrow.up{{color:var(--green)}}.rank-arrow.down{{color:var(--red)}}.rank-arrow.same{{color:var(--muted)}}
.rank-prev{{font-size:12px;color:var(--muted)}}
.cat-note{{background:linear-gradient(135deg,#eff6ff,#dbeafe);border:1px solid #93c5fd;border-radius:10px;padding:10px 18px;font-size:13px;color:#1e40af;font-weight:600;margin:14px 36px 0;display:none}}
.cat-note.show{{display:flex;align-items:center;gap:8px}}
.charts-grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px;padding:18px 36px 0}}
.chart-card{{background:var(--surface);border:1px solid var(--border);border-radius:15px;padding:26px;box-shadow:0 2px 12px rgba(13,59,142,.06)}}
.chart-title{{font-size:18px;font-weight:700;color:var(--text);margin-bottom:4px}}
.chart-sub{{font-size:13px;color:var(--muted);margin-bottom:20px;line-height:1.5}}
.chart-wrap{{position:relative;height:300px}}
.legend{{display:flex;gap:14px;flex-wrap:wrap;margin-top:16px;padding-top:14px;border-top:1px solid var(--border)}}
.li{{display:flex;align-items:center;gap:6px;font-size:13px;color:var(--muted);font-weight:500}}
.ld{{width:12px;height:12px;border-radius:3px;flex-shrink:0}}
.no-data{{display:flex;align-items:center;justify-content:center;height:300px;color:var(--muted);font-size:14px;flex-direction:column;gap:8px}}
.info-strip{{margin:18px 36px 0;background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:20px 26px;box-shadow:0 2px 8px rgba(13,59,142,.05)}}
.info-strip h4{{font-size:13px;font-weight:700;color:var(--b1);text-transform:uppercase;letter-spacing:.8px;margin-bottom:10px}}
.info-desc{{font-size:14px;color:var(--muted);line-height:1.7;margin-bottom:14px}}
.firsts{{display:flex;gap:12px;flex-wrap:wrap}}
.first-badge{{background:var(--surface2);border:1px solid var(--border);border-radius:9px;padding:8px 16px;font-size:14px}}
.first-badge span{{font-weight:700;color:var(--b1);display:block;font-size:10px;letter-spacing:.6px;text-transform:uppercase;margin-bottom:2px}}
.tbl-controls{{display:flex;gap:16px;padding:22px 36px 0;flex-wrap:wrap;align-items:flex-end}}
.search-wrap{{flex:1;min-width:220px;display:flex;flex-direction:column;gap:7px}}
.search-wrap label{{font-size:12px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;color:var(--muted)}}
.search-wrap input{{background:var(--surface2);border:1.5px solid var(--border);color:var(--text);padding:11px 14px;border-radius:9px;font-family:var(--font);font-size:15px;outline:none;transition:border-color .2s;width:100%}}
.search-wrap input:focus{{border-color:var(--b1);box-shadow:0 0 0 3px rgba(13,59,142,.1)}}
.tbl-wrap{{margin:18px 36px 36px;background:var(--surface);border:1px solid var(--border);border-radius:14px;overflow:auto;box-shadow:0 2px 12px rgba(13,59,142,.06)}}
table{{width:100%;border-collapse:collapse;font-size:14px}}
thead{{background:linear-gradient(135deg,#0d3b8e,#1a5fbc);color:#fff}}
thead th{{padding:14px 16px;text-align:left;font-size:12px;font-weight:700;letter-spacing:.7px;text-transform:uppercase;white-space:nowrap}}
thead th.num{{text-align:center}}
tbody tr{{border-bottom:1px solid var(--border);transition:background .15s}}
tbody tr:hover{{background:#f0f6ff}}
tbody tr:last-child{{border-bottom:none}}
td{{padding:13px 16px;vertical-align:middle}}
td.num{{text-align:center}}
.tbl-rep{{font-size:12px;color:var(--muted);font-weight:500;margin-bottom:2px}}
.tbl-ind{{font-weight:600;color:var(--text);line-height:1.4}}
.chip-score{{display:inline-block;background:linear-gradient(135deg,#e8f0fe,#c7d9fa);color:var(--b1);font-weight:700;font-size:13px;padding:4px 12px;border-radius:20px}}
.chip-rank{{display:inline-flex;font-weight:700;font-size:13px;color:#7c3aed;background:#f3f0ff;padding:4px 12px;border-radius:20px}}
.chip-year{{background:#f0f4f9;color:var(--muted);font-size:12px;font-weight:600;padding:3px 10px;border-radius:10px}}
.chip-cat{{font-size:11px;font-weight:700;padding:3px 10px;border-radius:10px;background:#f0fdf4;color:#15803d;border:1px solid #86efac}}
.chg-up{{color:var(--green);font-weight:600;font-size:13px}}
.chg-down{{color:var(--red);font-weight:600;font-size:13px}}
.chg-same{{color:var(--muted);font-weight:600;font-size:13px}}
.first-cell{{font-size:13px;color:var(--text);font-weight:500}}
.no-rows{{text-align:center;padding:44px;color:var(--muted);font-size:14px}}
.footer{{text-align:center;padding:18px;font-size:13px;color:var(--muted);border-top:1px solid var(--border);background:var(--surface);margin-top:20px}}
@media(max-width:900px){{
  .charts-grid{{grid-template-columns:1fr;padding:16px}}
  .pills,.kpi-row,.filter-section,.tbl-controls,.info-strip,.cat-note{{padding-left:16px;padding-right:16px}}
  .filter-section,.tbl-wrap{{margin-left:16px;margin-right:16px}}
  .hdr,.tabs{{padding-left:16px;padding-right:16px}}
  .tbl-wrap{{margin:16px}}
}}
</style>
</head>
<body>
<div class="hdr">
  <div class="flag">
    <div class="r"></div>
    <div class="s"><div class="g"></div><div class="w"></div><div class="b"></div></div>
  </div>
  <div class="hdr-txt" style="margin-left:8px">
    <h1>&#127462;&#127466; UAE Gender Balance Dashboard</h1>
    <p>Benchmarking UAE against G7 &middot; G20 &middot; GCC &middot; World across international gender indicators</p>
  </div>
  <div class="hdr-badge">Live Data</div>
</div>
<div class="tabs-bar">
  <div class="tabs">
    <div class="tab active" onclick="switchTab('dashboard',this)">&#128202; Dashboard</div>
    <div class="tab" onclick="switchTab('details',this)">&#128203; Indicator Details</div>
  </div>
</div>
<div id="panel-dashboard" class="panel active">
  <div class="pills">
    <div class="pill"><div class="pill-icon pi-b">&#128203;</div><div><div class="pill-num" id="pill-reports">—</div><div class="pill-lbl">Reports</div></div></div>
    <div class="pill"><div class="pill-icon pi-t">&#128202;</div><div><div class="pill-num" id="pill-inds">—</div><div class="pill-lbl">Indicators</div></div></div>
    <div class="pill"><div class="pill-icon pi-y">&#127757;</div><div><div class="pill-num" id="pill-cats">—</div><div class="pill-lbl">Categories</div></div></div>
  </div>
  <div class="filter-section">
    <div class="mode-toggle">
      <div class="mode-btn active" id="btn-cat" onclick="setMode('category')">&#127991;&#65039; By Category</div>
      <div class="mode-btn" id="btn-rep" onclick="setMode('report')">&#128193; By Report</div>
    </div>
    <div class="mode-panel active" id="mode-category">
      <div class="mode-label">&#127991;&#65039; Category</div>
      <div class="filter-row">
        <div class="fg" style="max-width:400px"><select id="catSel" onchange="renderCategory()"></select></div>
      </div>
      <div class="cat-indicator-count" id="catCount"></div>
    </div>
    <div class="mode-panel" id="mode-report">
      <div class="filter-row">
        <div class="fg"><div class="mode-label">&#128193; Report</div><select id="rSel" onchange="onReport()"></select></div>
        <div class="fg"><div class="mode-label">&#128269; Indicator</div><select id="iSel" onchange="renderIndicator()"></select></div>
      </div>
    </div>
  </div>
  <div class="cat-note" id="catNote"><span>&#128202;</span><span id="catNoteText">Showing averages across this category</span></div>
  <div class="kpi-row">
    <div class="kpi c1"><div class="kpi-lbl">&#127462;&#127466; UAE Score</div><div class="kpi-val" id="k-uae">—</div><div class="kpi-meta" id="k-yr"></div></div>
    <div class="kpi c2"><div class="kpi-lbl">G7 Average</div><div class="kpi-val" id="k-g7">—</div><div class="kpi-diff" id="d-g7"></div></div>
    <div class="kpi c3"><div class="kpi-lbl">G20 Average</div><div class="kpi-val" id="k-g20">—</div><div class="kpi-diff" id="d-g20"></div></div>
    <div class="kpi c4"><div class="kpi-lbl">GCC Average</div><div class="kpi-val" id="k-gcc">—</div><div class="kpi-diff" id="d-gcc"></div></div>
    <div class="kpi c5"><div class="kpi-lbl">World Average</div><div class="kpi-val" id="k-wld">—</div><div class="kpi-diff" id="d-wld"></div></div>
    <div class="kpi c6" id="kpi-rank-card">
      <div class="kpi-lbl">&#127942; UAE Global Rank</div>
      <div class="rank-row"><div class="rank-num" id="k-rank">—</div><div class="rank-of" id="k-rank-of"></div></div>
      <div class="rank-arrow" id="rank-arrow"></div>
      <div class="rank-prev" id="rank-prev"></div>
    </div>
    <div class="kpi c7"><div class="kpi-lbl">&#127757; Countries in Report</div><div class="kpi-val" id="k-ctry">—</div><div class="kpi-meta" id="k-ctry-lbl"></div></div>
    <div class="kpi c8"><div class="kpi-lbl">&#127970; Responsible Entity</div><div class="kpi-val" id="k-entity" style="font-size:15px;font-weight:700;line-height:1.4;margin-top:4px;word-break:break-word">—</div></div>
  </div>
  <div class="charts-grid">
    <div class="chart-card">
      <div class="chart-title">Score Comparison</div>
      <div class="chart-sub" id="bar-sub">UAE vs benchmark groups</div>
      <div class="chart-wrap"><canvas id="barC"></canvas><div class="no-data" id="barND" style="display:none">No data available</div></div>
      <div class="legend">
        <div class="li"><div class="ld" style="background:#0d3b8e"></div>UAE</div>
        <div class="li"><div class="ld" style="background:#1a5fbc"></div>G7</div>
        <div class="li"><div class="ld" style="background:#2e80d4"></div>G20</div>
        <div class="li"><div class="ld" style="background:#5aa8e8"></div>GCC</div>
        <div class="li"><div class="ld" style="background:#9ccbf4"></div>World</div>
      </div>
    </div>
    <div class="chart-card">
      <div class="chart-title">UAE Trend Over Time</div>
      <div class="chart-sub" id="trnd-sub">Historical UAE score</div>
      <div class="chart-wrap"><canvas id="trnC"></canvas><div class="no-data" id="trnND" style="display:none">Not enough trend data</div></div>
      <div class="legend"><div class="li"><div class="ld" style="background:#0d3b8e;border-radius:50%"></div>UAE Score</div></div>
    </div>
  </div>
  <div class="info-strip" id="infoStrip">
    <h4>&#8505;&#65039; About this Indicator</h4>
    <div class="info-desc" id="info-desc">Select an indicator to see its description.</div>
    <div class="firsts" id="info-firsts"></div>
  </div>
  <div class="footer">Sources: Women Business &amp; the Law &nbsp;&middot;&nbsp; Global Gender Gap Report &nbsp;&middot;&nbsp; Social Progress Index &nbsp;&middot;&nbsp; and more</div>
</div>
<div id="panel-details" class="panel">
  <div class="tbl-controls">
    <div class="fg" style="max-width:220px"><label>&#128193; Report</label><select id="tblRSel" onchange="renderTable()"></select></div>
    <div class="fg" style="max-width:220px"><label>&#127991;&#65039; Category</label><select id="tblCatSel" onchange="renderTable()"></select></div>
    <div class="search-wrap"><label>&#128269; Search</label><input type="text" id="tblSearch" placeholder="Search indicators..." oninput="renderTable()"></div>
  </div>
  <div class="tbl-wrap">
    <table>
      <thead><tr>
        <th>Report &nbsp;&middot;&nbsp; Indicator</th><th>Category</th>
        <th class="num">Year</th><th class="num">UAE Score</th><th class="num">Rank</th><th class="num">Change</th>
        <th>&#127760; First Globally</th><th>&#127757; First Arab</th><th>First GCC</th>
      </tr></thead>
      <tbody id="tblBody"></tbody>
    </table>
  </div>
</div>
<script>
const DATA={DATA_JS};
const REPORT_COUNTRIES={RC_JS};
const CATS={CATS_JS};
const IND_TO_CAT={{}};
Object.entries(CATS).forEach(([cat,inds])=>inds.forEach(ind=>IND_TO_CAT[ind]=cat));
const BLUES=['#0d3b8e','#1a5fbc','#2e80d4','#5aa8e8','#9ccbf4'];
const BLUES_B=['#0a2d70','#145099','#2570be','#4898d8','#8cbbec'];
let barChart=null,trnChart=null,currentMode='category';
function fmt(v){{if(v===null||v===undefined)return'—';if(v>=100)return v.toFixed(1);if(v>=10)return v.toFixed(1);if(v>=1)return v.toFixed(2);return v.toFixed(3);}}
function setDiff(uae,bench,el){{if(uae===null||bench===null||uae===undefined||bench===undefined){{el.textContent='';return;}}const d=uae-bench;el.textContent=(d>0.001?'▲ +':d<-0.001?'▼ -':'= ')+fmt(Math.abs(d))+' vs UAE';el.className='kpi-diff '+(d>0.001?'pos':d<-0.001?'neg':'neu');}}
function avgArr(arr){{const v=arr.filter(x=>x!==null&&x!==undefined&&!isNaN(x));return v.length?v.reduce((a,b)=>a+b,0)/v.length:null;}}
function switchTab(id,el){{document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));el.classList.add('active');document.getElementById('panel-'+id).classList.add('active');if(id==='details')renderTable();}}
function setMode(mode){{currentMode=mode;document.getElementById('btn-cat').classList.toggle('active',mode==='category');document.getElementById('btn-rep').classList.toggle('active',mode==='report');document.getElementById('mode-category').classList.toggle('active',mode==='category');document.getElementById('mode-report').classList.toggle('active',mode==='report');document.getElementById('infoStrip').style.display=mode==='report'?'block':'none';document.getElementById('catNote').classList.toggle('show',mode==='category');document.getElementById('kpi-rank-card').style.display=mode==='category'?'none':'flex';if(mode==='category')renderCategory();else renderIndicator();}}
function init(){{
  const reports=Object.keys(DATA.bar_data);
  const totalInds=Object.values(DATA.bar_data).reduce((s,v)=>s+Object.keys(v).length,0);
  document.getElementById('pill-reports').textContent=reports.length;
  document.getElementById('pill-inds').textContent=totalInds;
  document.getElementById('pill-cats').textContent=Object.keys(CATS).length;
  const cSel=document.getElementById('catSel');
  Object.keys(CATS).forEach(cat=>{{const o=document.createElement('option');o.value=o.textContent=cat;cSel.appendChild(o);}});
  const rSel=document.getElementById('rSel');
  reports.forEach(r=>{{const o=document.createElement('option');o.value=o.textContent=r;rSel.appendChild(o);}});
  fillInds(reports[0]);
  const tRSel=document.getElementById('tblRSel');
  let ao=document.createElement('option');ao.value='';ao.textContent='All Reports';tRSel.appendChild(ao);
  reports.forEach(r=>{{const o=document.createElement('option');o.value=o.textContent=r;tRSel.appendChild(o);}});
  const tCSel=document.getElementById('tblCatSel');
  ao=document.createElement('option');ao.value='';ao.textContent='All Categories';tCSel.appendChild(ao);
  Object.keys(CATS).forEach(cat=>{{const o=document.createElement('option');o.value=o.textContent=cat;tCSel.appendChild(o);}});
  document.getElementById('infoStrip').style.display='none';
  document.getElementById('catNote').classList.add('show');
  document.getElementById('kpi-rank-card').style.display='none';
  renderCategory();
}}
function fillInds(report){{const s=document.getElementById('iSel');s.innerHTML='';Object.keys(DATA.bar_data[report]||{{}}).sort().forEach(i=>{{const o=document.createElement('option');o.value=o.textContent=i;s.appendChild(o);}});}}
function onReport(){{fillInds(document.getElementById('rSel').value);renderIndicator();}}
function renderCategory(){{
  const cat=document.getElementById('catSel').value;
  const catInds=CATS[cat]||[];
  const entries=[];
  Object.values(DATA.bar_data).forEach(inds=>{{catInds.forEach(ind=>{{if(inds[ind])entries.push(inds[ind]);}});}});
  if(!entries.length)return;
  const uaeAvg=avgArr(entries.map(e=>e.UAE));
  const g7Avg=avgArr(entries.map(e=>e.G7_avg));
  const g20Avg=avgArr(entries.map(e=>e.G20_avg));
  const gccAvg=avgArr(entries.map(e=>e.GCC_avg));
  const worldAvg=avgArr(entries.map(e=>e.World_avg));
  document.getElementById('catCount').innerHTML='<span>'+entries.length+'</span> indicators in this category';
  document.getElementById('catNoteText').textContent='Showing average scores across '+entries.length+' indicators in "'+cat.replace(/^[^\\w]+\\s/,'')+'"';
  document.getElementById('k-uae').textContent=fmt(uaeAvg);
  document.getElementById('k-g7').textContent=fmt(g7Avg);
  document.getElementById('k-g20').textContent=fmt(g20Avg);
  document.getElementById('k-gcc').textContent=fmt(gccAvg);
  document.getElementById('k-wld').textContent=fmt(worldAvg);
  document.getElementById('k-yr').textContent='Average across '+entries.length+' indicators';
  setDiff(uaeAvg,g7Avg,document.getElementById('d-g7'));
  setDiff(uaeAvg,g20Avg,document.getElementById('d-g20'));
  setDiff(uaeAvg,gccAvg,document.getElementById('d-gcc'));
  setDiff(uaeAvg,worldAvg,document.getElementById('d-wld'));
  document.getElementById('k-ctry').textContent='—';
  document.getElementById('k-ctry-lbl').textContent='Multiple reports';
  document.getElementById('k-entity').textContent='—';
  document.getElementById('bar-sub').textContent='Average score — '+cat;
  drawBar([uaeAvg,g7Avg,g20Avg,gccAvg,worldAvg]);
  const yearMap={{}};
  Object.values(DATA.trend_data).forEach(repTrend=>{{catInds.forEach(ind=>{{if(!repTrend[ind])return;repTrend[ind].forEach(pt=>{{if(!yearMap[pt.year])yearMap[pt.year]=[];yearMap[pt.year].push(pt.score);}});}});}});
  const trendYears=Object.keys(yearMap).map(Number).sort((a,b)=>a-b);
  const trendScores=trendYears.map(y=>avgArr(yearMap[y]));
  document.getElementById('trnd-sub').textContent='Average UAE trajectory · '+trendYears[0]+' – '+trendYears[trendYears.length-1];
  drawTrend(trendYears,trendScores);
}}
function renderIndicator(){{
  const report=document.getElementById('rSel').value;
  const ind=document.getElementById('iSel').value;
  const bd=DATA.bar_data[report]?.[ind];
  const td=DATA.trend_data[report]?.[ind];
  if(!bd)return;
  document.getElementById('k-uae').textContent=fmt(bd.UAE);
  document.getElementById('k-g7').textContent=fmt(bd.G7_avg);
  document.getElementById('k-g20').textContent=fmt(bd.G20_avg);
  document.getElementById('k-gcc').textContent=fmt(bd.GCC_avg);
  document.getElementById('k-wld').textContent=fmt(bd.World_avg);
  document.getElementById('k-yr').textContent='Latest: '+bd.latest_year;
  setDiff(bd.UAE,bd.G7_avg,document.getElementById('d-g7'));
  setDiff(bd.UAE,bd.G20_avg,document.getElementById('d-g20'));
  setDiff(bd.UAE,bd.GCC_avg,document.getElementById('d-gcc'));
  setDiff(bd.UAE,bd.World_avg,document.getElementById('d-wld'));
  const total=REPORT_COUNTRIES[report]||'—';
  document.getElementById('k-rank').textContent=bd.rank&&bd.rank!=='-'?bd.rank:'—';
  document.getElementById('k-rank-of').textContent=bd.rank&&bd.rank!=='-'?' of '+total:'';
  document.getElementById('k-ctry').textContent=total;
  document.getElementById('k-ctry-lbl').textContent=report.length>32?report.slice(0,32)+'…':report;
  const arEl=document.getElementById('rank-arrow');
  const rd=bd.rank_diff||'';
  if(rd.includes('▲')){{arEl.textContent='▲ Improved '+rd.replace('▲','').trim()+' places';arEl.className='rank-arrow up';}}
  else if(rd.includes('▼')){{arEl.textContent='▼ Dropped '+rd.replace('▼','').trim()+' places';arEl.className='rank-arrow down';}}
  else{{arEl.textContent=rd==='►0'?'► No change':'';arEl.className='rank-arrow same';}}
  document.getElementById('rank-prev').textContent=bd.prev_rank&&bd.prev_rank!=='-'?'Previous: #'+bd.prev_rank:'';
  document.getElementById('k-entity').textContent=bd.entity&&bd.entity!=='-'&&bd.entity!=='Not Available'?bd.entity:'—';
  document.getElementById('bar-sub').textContent='"'+(ind.length>65?ind.slice(0,65)+'…':ind)+'" — '+bd.latest_year;
  document.getElementById('info-desc').textContent=bd.description||'No description available.';
  const fc=document.getElementById('info-firsts');fc.innerHTML='';
  [['🌐 Global',bd.first_global],['🌍 Arab',bd.first_arab],['🏳️ GCC',bd.first_gcc],['🏭 G20',bd.first_g20]].forEach(([lbl,val])=>{{
    if(!val||val==='-')return;
    const el=document.createElement('div');el.className='first-badge';
    el.innerHTML='<span>'+lbl+'</span>'+val;fc.appendChild(el);
  }});
  drawBar([bd.UAE,bd.G7_avg,bd.G20_avg,bd.GCC_avg,bd.World_avg]);
  if(!td||td.length<2){{document.getElementById('trnND').style.display='flex';document.getElementById('trnC').style.display='none';return;}}
  document.getElementById('trnd-sub').textContent='UAE trajectory · '+td[0].year+' – '+td[td.length-1].year;
  drawTrend(td.map(x=>x.year),td.map(x=>x.score));
}}
function drawBar(vals){{
  if(barChart)barChart.destroy();
  const hasData=vals.some(v=>v!==null&&v!==undefined);
  document.getElementById('barND').style.display=hasData?'none':'flex';
  document.getElementById('barC').style.display=hasData?'block':'none';
  if(!hasData)return;
  const dlPlugin={{id:'dl',afterDatasetsDraw(c){{const{{ctx,data}}=c;ctx.save();data.datasets.forEach((ds,di)=>{{c.getDatasetMeta(di).data.forEach((bar,ji)=>{{const v=ds.data[ji];if(v===null||v===undefined)return;ctx.font='700 13px Calibri,sans-serif';ctx.fillStyle=BLUES[ji];ctx.textAlign='center';ctx.textBaseline='bottom';ctx.fillText(fmt(v),bar.x,bar.y-4);}});}});ctx.restore();}}}};
  barChart=new Chart(document.getElementById('barC').getContext('2d'),{{type:'bar',plugins:[dlPlugin],data:{{labels:['🇦🇪 UAE','G7 Avg','G20 Avg','GCC Avg','World Avg'],datasets:[{{data:vals,backgroundColor:BLUES,borderColor:BLUES_B,borderWidth:1.5,borderRadius:7,borderSkipped:false}}]}},options:{{responsive:true,maintainAspectRatio:false,layout:{{padding:{{top:24}}}},plugins:{{legend:{{display:false}},tooltip:{{backgroundColor:'#fff',borderColor:'#dde4ef',borderWidth:1,titleColor:'#1a2340',bodyColor:'#0d3b8e',padding:10,callbacks:{{label:c=>'  Score: '+fmt(c.parsed.y)}}}}}},scales:{{x:{{grid:{{display:false}},ticks:{{color:'#7a8aaa',font:{{family:'Calibri,sans-serif',size:14,weight:'500'}}}}}},y:{{grid:{{color:'rgba(0,0,0,0.05)'}},ticks:{{color:'#7a8aaa',font:{{family:'Calibri,sans-serif',size:13}}}},beginAtZero:true}}}}}}}});
}}
function drawTrend(years,scores){{
  if(trnChart)trnChart.destroy();
  if(!years||years.length<2){{document.getElementById('trnND').style.display='flex';document.getElementById('trnC').style.display='none';return;}}
  document.getElementById('trnND').style.display='none';document.getElementById('trnC').style.display='block';
  const tCtx=document.getElementById('trnC').getContext('2d');
  const g=tCtx.createLinearGradient(0,0,0,300);g.addColorStop(0,'rgba(13,59,142,0.13)');g.addColorStop(1,'rgba(13,59,142,0.01)');
  trnChart=new Chart(tCtx,{{type:'line',data:{{labels:years,datasets:[{{label:'UAE',data:scores,borderColor:'#0d3b8e',backgroundColor:g,borderWidth:2.5,pointBackgroundColor:'#0d3b8e',pointBorderColor:'#fff',pointBorderWidth:2,pointRadius:4,pointHoverRadius:7,fill:true,tension:0.35}}]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}},tooltip:{{backgroundColor:'#fff',borderColor:'#dde4ef',borderWidth:1,titleColor:'#7a8aaa',bodyColor:'#0d3b8e',padding:10,callbacks:{{label:c=>'  UAE: '+fmt(c.parsed.y)}}}}}},scales:{{x:{{grid:{{display:false}},ticks:{{color:'#7a8aaa',font:{{family:'Calibri,sans-serif',size:13}},maxTicksLimit:10}}}},y:{{grid:{{color:'rgba(0,0,0,0.05)'}},ticks:{{color:'#7a8aaa',font:{{family:'Calibri,sans-serif',size:13}}}}}}}}}}}});
}}
function chgHTML(r){{if(!r||r==='-')return'<span class="chg-same">—</span>';if(r.includes('▲'))return'<span class="chg-up">▲ '+r.replace('▲','').trim()+'</span>';if(r.includes('▼'))return'<span class="chg-down">▼ '+r.replace('▼','').trim()+'</span>';return'<span class="chg-same">►</span>';}}
function renderTable(){{
  const fR=document.getElementById('tblRSel').value;
  const fCat=document.getElementById('tblCatSel').value;
  const q=(document.getElementById('tblSearch').value||'').toLowerCase();
  const tb=document.getElementById('tblBody');tb.innerHTML='';
  let n=0;
  Object.entries(DATA.bar_data).forEach(([rep,inds])=>{{
    if(fR&&rep!==fR)return;
    Object.entries(inds).forEach(([ind,bd])=>{{
      const cat=IND_TO_CAT[ind]||'—';
      if(fCat&&cat!==fCat)return;
      if(q&&!ind.toLowerCase().includes(q)&&!rep.toLowerCase().includes(q))return;
      n++;
      const tr=document.createElement('tr');
      tr.innerHTML='<td><div class="tbl-rep">'+rep+'</div><div class="tbl-ind">'+ind+'</div></td>'+
        '<td><span class="chip-cat">'+(cat!=='—'?cat:'—')+'</span></td>'+
        '<td class="num"><span class="chip-year">'+bd.latest_year+'</span></td>'+
        '<td class="num"><span class="chip-score">'+fmt(bd.UAE)+'</span></td>'+
        '<td class="num"><span class="chip-rank">'+(bd.rank&&bd.rank!=='-'?'#'+bd.rank:'—')+'</span></td>'+
        '<td class="num">'+chgHTML(bd.rank_diff)+'</td>'+
        '<td><div class="first-cell">'+(bd.first_global||'—')+'</div></td>'+
        '<td><div class="first-cell">'+(bd.first_arab||'—')+'</div></td>'+
        '<td><div class="first-cell">'+(bd.first_gcc||'—')+'</div></td>';
      tb.appendChild(tr);
    }});
  }});
  if(n===0){{const tr=document.createElement('tr');tr.innerHTML='<td colspan="9" class="no-rows">No indicators match your search.</td>';tb.appendChild(tr);}}
}}
init();
</script>
</body>
</html>"""

# Replace placeholders with actual data
HTML = HTML.replace("{DATA_JS}", DATA_JS).replace("{RC_JS}", RC_JS).replace("{CATS_JS}", CATS_JS)

Path("index.html").write_text(HTML, encoding="utf-8")
print(f"✅ index.html written ({len(HTML):,} bytes)")
