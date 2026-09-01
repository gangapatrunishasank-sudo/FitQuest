import streamlit as st


def apply_fitquest_theme():
    """Apply the shared FitQuest visual system to every Streamlit page."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');

    :root {
        --fq-bg: #070A12;
        --fq-panel: rgba(16, 21, 36, .82);
        --fq-panel-2: #101526;
        --fq-text: #F5F7FF;
        --fq-muted: #98A2B8;
        --fq-cyan: #22D3EE;
        --fq-violet: #8B5CF6;
        --fq-pink: #F472B6;
        --fq-green: #34D399;
        --fq-border: rgba(148, 163, 184, .16);
    }

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp {
        background:
          radial-gradient(circle at 10% 5%, rgba(34,211,238,.10), transparent 26%),
          radial-gradient(circle at 90% 10%, rgba(139,92,246,.13), transparent 28%),
          linear-gradient(180deg, #070A12 0%, #090D18 55%, #070A12 100%);
        color: var(--fq-text);
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(10,14,26,.98), rgba(7,10,18,.98));
        border-right: 1px solid var(--fq-border);
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.2rem; }
    .block-container { max-width: 1400px; padding-top: 2rem; padding-bottom: 4rem; }
    h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; letter-spacing: -.035em; }
    h1 { font-weight: 700; }
    .fq-brand { display:flex; align-items:center; gap:.65rem; margin-bottom:1.5rem; }
    .fq-mark { width:42px; height:42px; border-radius:13px; display:grid; place-items:center; background:linear-gradient(135deg,var(--fq-cyan),var(--fq-violet)); box-shadow:0 0 35px rgba(34,211,238,.22); font-size:1.35rem; }
    .fq-brand-title { font:700 1.15rem 'Space Grotesk',sans-serif; }
    .fq-brand-sub { color:var(--fq-muted); font-size:.72rem; margin-top:-2px; }
    .fq-hero { position:relative; overflow:hidden; border:1px solid var(--fq-border); border-radius:28px; padding:3.4rem 3.5rem; background:linear-gradient(135deg,rgba(20,28,48,.92),rgba(13,17,30,.86)); box-shadow:0 30px 80px rgba(0,0,0,.28); }
    .fq-hero:after { content:''; position:absolute; width:320px; height:320px; right:-100px; top:-120px; border-radius:50%; background:radial-gradient(circle,rgba(139,92,246,.35),transparent 68%); }
    .fq-eyebrow { color:var(--fq-cyan); font-size:.78rem; font-weight:800; letter-spacing:.16em; text-transform:uppercase; }
    .fq-hero-title { font:700 clamp(2.5rem,6vw,5.5rem)/.94 'Space Grotesk',sans-serif; margin:.8rem 0 1.2rem; max-width:850px; }
    .fq-gradient { background:linear-gradient(90deg,var(--fq-cyan),#A78BFA,var(--fq-pink)); -webkit-background-clip:text; background-clip:text; color:transparent; }
    .fq-lead { color:#B8C1D6; font-size:1.05rem; line-height:1.75; max-width:720px; }
    .fq-card { border:1px solid var(--fq-border); background:linear-gradient(180deg,rgba(17,23,40,.82),rgba(11,15,27,.82)); border-radius:20px; padding:1.25rem; box-shadow:0 16px 40px rgba(0,0,0,.18); }
    .fq-card:hover { border-color:rgba(34,211,238,.28); }
    .fq-card-title { font:600 1.05rem 'Space Grotesk',sans-serif; margin-bottom:.35rem; }
    .fq-muted { color:var(--fq-muted); }
    .fq-kpi { border:1px solid var(--fq-border); border-radius:18px; padding:1.15rem 1.2rem; background:rgba(14,19,33,.82); }
    .fq-kpi-label { color:var(--fq-muted); font-size:.75rem; text-transform:uppercase; letter-spacing:.08em; }
    .fq-kpi-value { font:700 1.8rem 'Space Grotesk',sans-serif; margin-top:.25rem; }
    .fq-kpi-accent { color:var(--fq-cyan); }
    .fq-section { margin:2rem 0 1rem; }
    .fq-pill { display:inline-block; border:1px solid rgba(34,211,238,.25); background:rgba(34,211,238,.08); color:#9BEAF7; padding:.35rem .7rem; border-radius:999px; font-size:.75rem; font-weight:700; }
    .fq-feature-icon { font-size:1.8rem; margin-bottom:.7rem; }
    .fq-login { max-width:520px; margin:3rem auto 0; }
    .fq-login-head { text-align:center; margin-bottom:1.3rem; }
    .fq-login-title { font:700 2.1rem 'Space Grotesk',sans-serif; }
    .fq-login-copy { color:var(--fq-muted); }
    .stButton > button { border-radius:12px; min-height:2.75rem; font-weight:700; border:1px solid var(--fq-border); background:#11182A; }
    .stButton > button:hover { border-color:rgba(34,211,238,.45); color:white; box-shadow:0 0 24px rgba(34,211,238,.12); }
    button[kind="primary"] { background:linear-gradient(135deg,#06B6D4,#7C3AED) !important; border:0 !important; box-shadow:0 10px 30px rgba(124,58,237,.22); }
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div, .stNumberInput input { background:#0D1322 !important; border-color:var(--fq-border) !important; color:var(--fq-text) !important; border-radius:12px !important; }
    .stTabs [data-baseweb="tab-list"] { gap:8px; }
    .stTabs [data-baseweb="tab"] { border-radius:10px; padding:8px 16px; }
    .stProgress > div > div > div > div { background:linear-gradient(90deg,var(--fq-cyan),var(--fq-violet)); }
    [data-testid="stMetric"] { background:rgba(14,19,33,.7); border:1px solid var(--fq-border); padding:1rem; border-radius:16px; }
    .fq-footer { text-align:center; color:#69758C; padding:2.5rem 0 1rem; font-size:.78rem; }
    </style>
    """, unsafe_allow_html=True)


def brand(compact=False):
    st.markdown("""
    <div class="fq-brand">
      <div class="fq-mark">⚡</div>
      <div><div class="fq-brand-title">FITQUEST <span class="fq-gradient">AI</span></div>
      <div class="fq-brand-sub">COMPUTER VISION • GAMIFICATION</div></div>
    </div>
    """, unsafe_allow_html=True)


def section_heading(title, subtitle=None):
    st.markdown(f'<div class="fq-section"><h2>{title}</h2>' + (f'<div class="fq-muted">{subtitle}</div>' if subtitle else '') + '</div>', unsafe_allow_html=True)


def kpi(label, value, accent=False):
    cls='fq-kpi-accent' if accent else ''
    return f'<div class="fq-kpi"><div class="fq-kpi-label">{label}</div><div class="fq-kpi-value {cls}">{value}</div></div>'
