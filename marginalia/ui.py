"""Pure presentation helpers and theme styles."""

from __future__ import annotations

from html import escape


def normalize_tags(value: str) -> str:
    parts = [part.strip() for part in value.replace("，", ",").split(",") if part.strip()]
    return ", ".join(dict.fromkeys(parts))


def display_tags(value: str) -> str:
    return "".join(f'<span class="note-tag">{escape(tag.strip())}</span>' for tag in value.split(",") if tag.strip())


def excerpt(value: object, length: int = 120) -> str:
    text = str(value or "").strip()
    if not text:
        return "—"
    return text if len(text) <= length else text[: length - 1].rstrip() + "…"


APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@600;700&family=Source+Serif+4:opsz,wght@8..60,500;8..60,650&display=swap');
:root{--paper:#f7f3e9;--card:#fffdf8;--ink:#2c2924;--muted:#777166;--brown:#95683d;--brown-dark:#6f4928;--green:#355f4b;--line:#e2dacb}
.stApp{background:radial-gradient(circle at 78% 4%,rgba(213,190,151,.17),transparent 28%),var(--paper);color:var(--ink)}
[data-testid="stSidebar"]{background:#eee8dc;border-right:1px solid var(--line)}
[data-testid="stSidebar"]>div:first-child{padding:2.1rem 1.35rem}
[data-testid="stSidebar"] .stMarkdown h1{font-family:'Source Serif 4','Noto Serif SC',serif;color:var(--brown-dark);font-size:2rem;line-height:1.1;margin-bottom:.35rem;letter-spacing:-.035em}
[data-testid="stSidebar"] h1{font-size:2rem!important;line-height:1.15!important;font-weight:700!important}
[data-testid="stSidebarNav"]{display:none}
[data-testid="stSidebar"] div[role="radiogroup"]{gap:.34rem}
[data-testid="stSidebar"] div[role="radiogroup"] label{padding:.44rem .2rem;border-radius:9px;transition:background .15s ease}
[data-testid="stSidebar"] div[role="radiogroup"] label:hover{background:rgba(149,104,61,.08)}
[data-testid="stSidebar"] div[role="radiogroup"] label p{font-size:1.06rem!important;font-weight:620;line-height:1.5;color:#403b34}
[data-testid="stSidebar"] div[role="radiogroup"] label [data-testid="stMarkdownContainer"]{font-size:1.06rem}
[data-testid="stSidebar"] [data-testid="stRadioOption"]{padding:.52rem .25rem!important}
[data-testid="stSidebar"] [data-testid="stRadioOption"] p{font-size:1.15rem!important;line-height:1.45!important;font-weight:620!important}
.sidebar-subtitle{font-size:1rem;line-height:1.45;color:#6e675d;margin-bottom:.55rem}.sidebar-subtitle span{font-size:.66rem;font-weight:750;letter-spacing:.18em;color:var(--brown)}
.sidebar-info-card{background:rgba(255,253,248,.76);border:1px solid var(--line);border-radius:13px;padding:1rem 1.05rem;color:var(--ink)}
.sidebar-info-card strong{font:650 1.75rem 'Source Serif 4',Georgia,serif;color:var(--brown-dark);margin-right:.35rem}.sidebar-info-card span{font-size:.9rem;font-weight:650}.sidebar-info-card small{display:block;color:var(--muted);font-size:.82rem;line-height:1.7;margin-top:.55rem;padding-top:.55rem;border-top:1px solid var(--line)}
h1,h2,h3{font-family:'Source Serif 4','Noto Serif SC',Georgia,serif!important;color:var(--ink)!important;letter-spacing:-.02em}
.block-container{max-width:1180px;padding-top:2.2rem;padding-bottom:4rem}
.eyebrow{color:var(--brown);font-size:.72rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase;margin-bottom:.35rem}
.page-lead{color:var(--muted);font-size:1rem;margin-top:-.35rem;margin-bottom:1.7rem}
.hero-card{padding:1.8rem 2rem;border-radius:18px;background:linear-gradient(120deg,#6f4928,#95683d 56%,#b48757);color:#fff8ed;box-shadow:0 16px 38px rgba(89,61,35,.16);margin-bottom:1.4rem;position:relative;overflow:hidden}
.hero-card:after{content:'Aa';position:absolute;right:1.2rem;bottom:-1.6rem;font:700 7rem Georgia;color:rgba(255,255,255,.08)}
.hero-card h2{color:#fffaf1!important;margin:.25rem 0 .4rem;font-size:2.05rem}.hero-card p{margin:0;opacity:.84;max-width:630px}
.metric-card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:1.05rem 1.2rem;box-shadow:0 5px 18px rgba(80,63,43,.05);min-height:105px}
.metric-card .value{font:650 2rem 'Source Serif 4',Georgia,serif;color:var(--brown-dark)}.metric-card .label{font-size:.78rem;color:var(--muted);letter-spacing:.06em}
.entry-card{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--brown);border-radius:13px;padding:1.05rem 1.2rem;margin:.65rem 0;box-shadow:0 4px 15px rgba(65,50,34,.045)}
.entry-card.sentence{border-left-color:var(--green)}.entry-card .entry-title{font:650 1.12rem 'Source Serif 4','Noto Serif SC',serif;color:var(--ink);margin-bottom:.35rem}.entry-card .entry-meta{font-size:.76rem;color:var(--muted);margin-top:.6rem}.entry-card .entry-copy{color:#5d584f;line-height:1.65;font-size:.9rem}
.note-tag{display:inline-block;background:#efe2cf;color:#79502d;border-radius:999px;padding:.18rem .55rem;margin:.35rem .28rem 0 0;font-size:.7rem;font-weight:600}
.status-pill{display:inline-block;background:#e2ece5;color:#355f4b;border-radius:999px;padding:.18rem .55rem;font-size:.7rem;font-weight:700}
.import-note{background:#fffaf0;border:1px solid var(--line);border-left:4px solid var(--brown);border-radius:12px;padding:1rem 1.1rem;margin:.2rem 0 .75rem;color:#5d554a;line-height:1.7}
.section-rule{height:1px;background:var(--line);margin:1.3rem 0}
.stButton>button,.stFormSubmitButton>button{border-radius:10px;border:1px solid var(--brown)!important;background:var(--brown)!important;color:white!important;font-weight:650;padding:.45rem 1.1rem}
.stButton>button:hover,.stFormSubmitButton>button:hover{background:var(--brown-dark)!important;border-color:var(--brown-dark)!important}
[data-baseweb="input"]>div,[data-baseweb="textarea"]>div,[data-baseweb="select"]>div{background:var(--card)!important;border-color:var(--line)!important}
div[data-testid="stExpander"]{background:rgba(255,253,248,.62);border-color:var(--line);border-radius:12px}
#MainMenu,footer{visibility:hidden}
</style>
"""
