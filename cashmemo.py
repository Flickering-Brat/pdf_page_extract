import streamlit as st
import fitz  # PyMuPDF
import io
import re
from datetime import datetime

st.set_page_config(
    page_title="Smart Invoice Extractor",
    page_icon="⛽",
    layout="centered"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Share+Tech+Mono&family=Exo+2:ital,wght@0,300;0,400;0,600;1,300&display=swap');

/* ╔══════════════════════════════════════════╗
   ║  HARD DARK THEME — survives light mode  ║
   ╚══════════════════════════════════════════╝ */
html { color-scheme: dark !important; }

html, body { background: #03080f !important; }

.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
section[data-testid="stMain"],
section.main,
.main { background: #03080f !important; }

[data-testid="stHeader"]          { background: #03080f !important; border-bottom: 1px solid rgba(0,140,255,0.12) !important; }
[data-testid="stToolbar"]         { background: transparent !important; }
[data-testid="stDecoration"]      { display: none !important; }
[data-testid="stStatusWidget"]    { color: #3a7bd5 !important; }

/* ╔══════════════════════════════════════════╗
   ║  ANIMATED BACKGROUND MESH               ║
   ╚══════════════════════════════════════════╝ */
.stApp {
    background:
        radial-gradient(ellipse 100% 60% at 50% -8%,  rgba(0,140,255,0.14) 0%, transparent 65%),
        radial-gradient(ellipse 50%  40% at 92% 88%,  rgba(255,85,0,0.08)  0%, transparent 55%),
        radial-gradient(ellipse 35%  28% at 4%  72%,  rgba(0,220,255,0.05) 0%, transparent 50%),
        #03080f !important;
    min-height: 100vh;
    position: relative;
}

/* Animated scanlines */
.stApp::before {
    content: '';
    position: fixed; inset: 0;
    background: repeating-linear-gradient(
        0deg,
        transparent 0px, transparent 3px,
        rgba(0,160,255,0.018) 3px, rgba(0,160,255,0.018) 4px
    );
    pointer-events: none;
    z-index: 0;
    animation: scanmove 8s linear infinite;
}

@keyframes scanmove {
    0%   { background-position: 0 0; }
    100% { background-position: 0 80px; }
}

/* Drifting ambient orbs */
.stApp::after {
    content: '';
    position: fixed; inset: 0;
    background:
        radial-gradient(circle 300px at 20% 30%, rgba(0,140,255,0.04) 0%, transparent 70%),
        radial-gradient(circle 200px at 80% 70%, rgba(255,100,0,0.03) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
    animation: orbdrift 18s ease-in-out infinite alternate;
}

@keyframes orbdrift {
    0%   { transform: translate(0,   0);   opacity: 0.6; }
    50%  { transform: translate(30px, 20px); opacity: 1;   }
    100% { transform: translate(-20px, 35px); opacity: 0.7; }
}

/* ╔══════════════════════════════════════════╗
   ║  LAYOUT                                 ║
   ╚══════════════════════════════════════════╝ */
.block-container {
    max-width: 800px !important;
    padding: 2.6rem 2rem 5rem !important;
    position: relative; z-index: 1;
}

* { box-sizing: border-box; }

html, body, p, div, span, label, input,
[class*="css"], [class*="st-"] {
    font-family: 'Exo 2', sans-serif !important;
}

/* ╔══════════════════════════════════════════╗
   ║  HEADER                                 ║
   ╚══════════════════════════════════════════╝ */
.app-header {
    text-align: center;
    padding-bottom: 2.4rem;
    margin-bottom: 2.6rem;
    position: relative;
}

/* Live status pill */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(0,140,255,0.09);
    border: 1px solid rgba(0,140,255,0.28);
    border-radius: 20px;
    padding: 0.22rem 0.85rem;
    margin-bottom: 1.3rem;
}

.status-dot {
    width: 6px; height: 6px;
    background: #00d4ff;
    border-radius: 50%;
    box-shadow: 0 0 8px #00d4ff, 0 0 16px rgba(0,212,255,0.4);
    animation: livepulse 1.8s ease-in-out infinite;
}

@keyframes livepulse {
    0%, 100% { box-shadow: 0 0 6px #00d4ff, 0 0 12px rgba(0,212,255,0.3); transform: scale(1); }
    50%       { box-shadow: 0 0 12px #00d4ff, 0 0 24px rgba(0,212,255,0.6); transform: scale(1.25); }
}

.status-text {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.6rem !important;
    letter-spacing: 0.3em;
    color: rgba(0,200,255,0.85) !important;
    text-transform: uppercase;
}

/* Main title with shimmer animation */
.app-title {
    font-family: 'Rajdhani', sans-serif !important;
    font-size: clamp(1.9rem, 5vw, 3rem);
    font-weight: 700;
    letter-spacing: 0.07em;
    line-height: 1;
    margin: 0 0 0.55rem;
    background: linear-gradient(
        120deg,
        #c8e8ff 0%, #ffffff 20%,
        #5bc8ff 40%, #ffffff 55%,
        #ff8840 75%, #ffb060 85%,
        #c8e8ff 100%
    );
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: shimmer 4s linear infinite;
}

@keyframes shimmer {
    0%   { background-position: 0%   center; }
    100% { background-position: 200% center; }
}

.app-subtitle {
    font-family: 'Exo 2', sans-serif !important;
    font-size: 0.78rem !important;
    font-weight: 300;
    font-style: italic;
    color: rgba(130,180,230,0.5) !important;
    letter-spacing: 0.13em;
    margin: 0;
}

/* Glowing separator */
.header-sep {
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 1px;
    overflow: visible;
}

.header-sep::before {
    content: '';
    display: block;
    height: 1px;
    background: linear-gradient(90deg,
        transparent 0%, rgba(0,140,255,0.15) 10%,
        rgba(0,168,255,0.8) 50%,
        rgba(0,140,255,0.15) 90%, transparent 100%
    );
    animation: sepdrift 3s ease-in-out infinite alternate;
}

@keyframes sepdrift {
    0%   { opacity: 0.6; filter: blur(0px); }
    100% { opacity: 1.0; filter: blur(0.5px); }
}

.header-sep::after {
    content: '⛽';
    position: absolute;
    left: 50%; top: -0.65rem;
    transform: translateX(-50%);
    background: #03080f;
    padding: 0 0.7rem;
    font-size: 0.9rem;
    filter: drop-shadow(0 0 6px rgba(0,180,255,0.5));
}

/* ╔══════════════════════════════════════════╗
   ║  STEP PANELS                            ║
   ╚══════════════════════════════════════════╝ */
.sp {
    position: relative;
    background: linear-gradient(145deg,
        rgba(0,130,255,0.055) 0%,
        rgba(0,60,120,0.03)  100%
    );
    border: 1px solid rgba(0,140,255,0.2);
    border-radius: 10px;
    padding: 1.5rem 1.9rem 1.7rem;
    margin-bottom: 1.1rem;
    overflow: hidden;
    transition: border-color 0.3s, box-shadow 0.3s;
}

.sp:hover {
    border-color: rgba(0,168,255,0.38);
    box-shadow: 0 0 32px rgba(0,140,255,0.07), 0 4px 20px rgba(0,0,0,0.25);
}

/* Animated top accent bar */
.sp::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg,
        transparent 0%, rgba(0,168,255,0.0) 10%,
        #00a8ff 50%,
        rgba(0,168,255,0.0) 90%, transparent 100%
    );
    box-shadow: 0 0 10px rgba(0,168,255,0.4);
    animation: topbar 3s ease-in-out infinite alternate;
}

@keyframes topbar {
    0%   { opacity: 0.5; }
    100% { opacity: 1.0; }
}

/* Corner glow */
.sp::after {
    content: '';
    position: absolute;
    top: -30px; right: -30px;
    width: 100px; height: 100px;
    background: radial-gradient(circle, rgba(0,168,255,0.06) 0%, transparent 70%);
    pointer-events: none;
}

.sp-tag {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 1.15rem;
}

.sp-num {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.55rem !important;
    color: #00c8ff !important;
    background: rgba(0,200,255,0.1);
    border: 1px solid rgba(0,200,255,0.3);
    border-radius: 3px;
    padding: 0.12rem 0.42rem;
    letter-spacing: 0.12em;
    box-shadow: 0 0 6px rgba(0,200,255,0.15);
}

.sp-title {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.58rem !important;
    letter-spacing: 0.3em;
    color: rgba(110,170,225,0.6) !important;
    text-transform: uppercase;
}

/* ╔══════════════════════════════════════════╗
   ║  FILE UPLOADER                          ║
   ╚══════════════════════════════════════════╝ */
[data-testid="stFileUploader"] > label,
[data-testid="stFileUploaderDropzone"] > label {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    overflow: hidden !important;
}

[data-testid="stFileUploader"] section,
[data-testid="stFileUploaderDropzone"] {
    background: rgba(0,130,255,0.05) !important;
    border: 1px dashed rgba(0,140,255,0.42) !important;
    border-radius: 8px !important;
    padding: 1.8rem !important;
    transition: all 0.3s ease !important;
}

[data-testid="stFileUploader"] section:hover {
    border-color: rgba(0,200,255,0.75) !important;
    background: rgba(0,140,255,0.09) !important;
    box-shadow: 0 0 24px rgba(0,168,255,0.08) inset,
                0 0 16px rgba(0,168,255,0.06) !important;
}

[data-testid="stFileUploader"] section *,
[data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] p,
[data-testid="stFileUploader"] button {
    color: rgba(120,180,240,0.7) !important;
    font-family: 'Exo 2', sans-serif !important;
}

[data-testid="stFileUploaderFile"] {
    background: rgba(0,140,255,0.09) !important;
    border: 1px solid rgba(0,168,255,0.3) !important;
    border-radius: 5px !important;
}

/* ╔══════════════════════════════════════════╗
   ║  TEXT INPUTS                            ║
   ╚══════════════════════════════════════════╝ */
.stTextInput label,
.stTextInput > div > label {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.58rem !important;
    letter-spacing: 0.28em !important;
    text-transform: uppercase !important;
    color: rgba(110,168,220,0.6) !important;
}

.stTextInput input,
.stTextInput > div > div > input {
    background: rgba(0,130,255,0.07) !important;
    border: 1px solid rgba(0,140,255,0.3) !important;
    border-radius: 6px !important;
    color: #b8dcff !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.98rem !important;
    letter-spacing: 0.07em !important;
    padding: 0.58rem 1rem !important;
    transition: all 0.2s ease !important;
    caret-color: #00d4ff;
}

.stTextInput input:focus,
.stTextInput > div > div > input:focus {
    border-color: rgba(0,200,255,0.75) !important;
    background: rgba(0,140,255,0.11) !important;
    box-shadow: 0 0 0 3px rgba(0,180,255,0.1),
                0 0 18px rgba(0,180,255,0.1) !important;
    outline: none !important;
}

/* ╔══════════════════════════════════════════╗
   ║  BUTTONS                                ║
   ╚══════════════════════════════════════════╝ */
.stButton > button,
.stButton button {
    width: 100% !important;
    background: linear-gradient(135deg,
        rgba(0,140,255,0.18) 0%,
        rgba(0,90,190,0.09)  100%) !important;
    border: 1px solid rgba(0,168,255,0.52) !important;
    border-radius: 6px !important;
    color: #55ccff !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    padding: 0.72rem 1.5rem !important;
    cursor: pointer !important;
    transition: all 0.22s ease !important;
    position: relative !important;
    overflow: hidden !important;
}

.stButton > button::after,
.stButton button::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, transparent 60%);
    pointer-events: none;
}

.stButton > button:hover,
.stButton button:hover {
    border-color: rgba(0,220,255,0.85) !important;
    color: #ffffff !important;
    box-shadow:
        0 0 0 1px rgba(0,210,255,0.18),
        0 0 30px rgba(0,168,255,0.28),
        0 6px 18px rgba(0,0,0,0.5) !important;
    transform: translateY(-2px) !important;
}

.stButton > button:active,
.stButton button:active {
    transform: translateY(0) !important;
    box-shadow: 0 0 14px rgba(0,168,255,0.2) !important;
}

/* Download — amber */
[data-testid="stDownloadButton"] > button,
[data-testid="stDownloadButton"] button {
    background: linear-gradient(135deg,
        rgba(255,100,0,0.18) 0%,
        rgba(200,65,0,0.09)  100%) !important;
    border: 1px solid rgba(255,110,0,0.52) !important;
    color: #ffaa50 !important;
}

[data-testid="stDownloadButton"] > button:hover,
[data-testid="stDownloadButton"] button:hover {
    border-color: rgba(255,145,0,0.9) !important;
    color: #ffffff !important;
    box-shadow:
        0 0 0 1px rgba(255,120,0,0.2),
        0 0 30px rgba(255,100,0,0.28),
        0 6px 18px rgba(0,0,0,0.5) !important;
    transform: translateY(-2px) !important;
}

/* ╔══════════════════════════════════════════╗
   ║  PROGRESS BAR                           ║
   ╚══════════════════════════════════════════╝ */
.stProgress > div > div {
    background: rgba(0,130,255,0.12) !important;
    border: 1px solid rgba(0,140,255,0.2) !important;
    border-radius: 4px !important;
    height: 6px !important;
}

.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #003878, #007fdf, #00d4ff) !important;
    box-shadow: 0 0 12px rgba(0,210,255,0.6),
                0 0  6px rgba(0,210,255,0.3) !important;
    border-radius: 4px !important;
    animation: progressglow 1.5s ease-in-out infinite alternate;
}

@keyframes progressglow {
    0%   { box-shadow: 0 0 10px rgba(0,210,255,0.5); }
    100% { box-shadow: 0 0 18px rgba(0,210,255,0.85), 0 0 30px rgba(0,168,255,0.35); }
}

/* ╔══════════════════════════════════════════╗
   ║  EXPANDER / LOG                         ║
   ╚══════════════════════════════════════════╝ */
[data-testid="stExpander"] {
    background: rgba(0,12,28,0.75) !important;
    border: 1px solid rgba(0,140,255,0.2) !important;
    border-radius: 8px !important;
}

[data-testid="stExpander"] summary,
[data-testid="stExpander"] details > summary {
    color: rgba(90,165,235,0.7) !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.6rem !important;
    letter-spacing: 0.28em !important;
    text-transform: uppercase !important;
    padding: 0.7rem 1rem !important;
    background: transparent !important;
}

[data-testid="stExpander"] p,
[data-testid="stExpander"] pre,
[data-testid="stExpander"] code {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.7rem !important;
    color: rgba(110,175,235,0.7) !important;
    line-height: 1.7 !important;
}

/* ╔══════════════════════════════════════════╗
   ║  ALERTS                                 ║
   ╚══════════════════════════════════════════╝ */
div[data-testid="stAlert"],
.stAlert > div {
    border-radius: 7px !important;
    font-family: 'Exo 2', sans-serif !important;
    font-size: 0.87rem !important;
}

.stSuccess, [data-baseweb="notification"][kind="positive"] {
    background: rgba(0,210,90,0.08) !important;
    border: 1px solid rgba(0,210,80,0.35) !important;
    color: #60ffaa !important;
}

.stError, [data-baseweb="notification"][kind="negative"] {
    background: rgba(255,50,50,0.08) !important;
    border: 1px solid rgba(255,60,50,0.35) !important;
    color: #ffaaaa !important;
}

/* ╔══════════════════════════════════════════╗
   ║  MISC TEXT                              ║
   ╚══════════════════════════════════════════╝ */
p, .stText p, [data-testid="stText"] {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.72rem !important;
    color: rgba(110,170,225,0.65) !important;
    line-height: 1.65 !important;
}

/* ╔══════════════════════════════════════════╗
   ║  RESULT STATS                           ║
   ╚══════════════════════════════════════════╝ */
.result-stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin: 1.5rem 0 1.3rem;
}

.stat-tile {
    position: relative;
    background: linear-gradient(145deg, rgba(0,130,255,0.08), rgba(0,70,150,0.04));
    border: 1px solid rgba(0,140,255,0.24);
    border-radius: 8px;
    padding: 1.1rem 0.8rem;
    text-align: center;
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
    animation: fadein 0.5s ease both;
}

.stat-tile:nth-child(1) { animation-delay: 0.0s; }
.stat-tile:nth-child(2) { animation-delay: 0.1s; }
.stat-tile:nth-child(3) { animation-delay: 0.2s; }

@keyframes fadein {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0);    }
}

.stat-tile:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 24px rgba(0,140,255,0.15);
}

.stat-tile::before {
    content: '';
    position: absolute;
    top: 0; left: 15%; right: 15%;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0,200,255,0.6), transparent);
    box-shadow: 0 0 6px rgba(0,200,255,0.3);
}

.stat-value {
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 2.2rem !important;
    font-weight: 700;
    color: #38d0ff !important;
    line-height: 1;
    text-shadow: 0 0 22px rgba(0,210,255,0.45);
}

.stat-label {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.5rem !important;
    letter-spacing: 0.22em;
    color: rgba(90,155,215,0.55) !important;
    text-transform: uppercase;
    margin-top: 0.35rem;
}

/* ╔══════════════════════════════════════════╗
   ║  COLUMNS + SCROLLBAR                    ║
   ╚══════════════════════════════════════════╝ */
[data-testid="stHorizontalBlock"] { gap: 1rem !important; }

::-webkit-scrollbar              { width: 3px; height: 3px; }
::-webkit-scrollbar-track        { background: #03080f; }
::-webkit-scrollbar-thumb        { background: rgba(0,168,255,0.3); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover  { background: rgba(0,200,255,0.6); }
</style>
""", unsafe_allow_html=True)


# ── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <div style="display:flex; justify-content:center; margin-bottom:1.2rem;">
        <div class="status-pill">
            <div class="status-dot"></div>
            <span class="status-text">Indian Oil Corporation Ltd &nbsp;·&nbsp; Document Processing Unit</span>
        </div>
    </div>
    <div class="app-title">SMART INVOICE EXTRACTOR</div>
    <p class="app-subtitle">High-Speed Bulk PDF Extraction &amp; A4 Packing Engine</p>
    <div class="header-sep"></div>
</div>
""", unsafe_allow_html=True)


# ── PANEL 01 — UPLOAD ────────────────────────────────────────────────────────
st.markdown("""
<div class="sp">
    <div class="sp-tag">
        <span class="sp-num">01</span>
        <span class="sp-title">Document Source</span>
    </div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Drop your bulk PDF here",
    type="pdf",
    label_visibility="collapsed"
)

st.markdown("</div>", unsafe_allow_html=True)


# ── PANELS 02 & 03 — after file upload ───────────────────────────────────────
if uploaded_file:

    st.markdown("""
    <div class="sp">
        <div class="sp-tag">
            <span class="sp-num">02</span>
            <span class="sp-title">Date Filter Range</span>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        start_str = st.text_input("From Date (DD-MM-YYYY)", "01-03-2026")
    with col2:
        end_str = st.text_input("To Date (DD-MM-YYYY)", "20-03-2026")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="sp">
        <div class="sp-tag">
            <span class="sp-num">03</span>
            <span class="sp-title">Execute</span>
        </div>
    """, unsafe_allow_html=True)

    run = st.button("⚡  INITIATE EXTRACTION SEQUENCE")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── PROCESSING ───────────────────────────────────────────────────────────
    if run:
        try:
            start_date = datetime.strptime(start_str, "%d-%m-%Y")
            end_date   = datetime.strptime(end_str,   "%d-%m-%Y")

            file_bytes = uploaded_file.getvalue()
            doc        = fitz.open(stream=file_bytes, filetype="pdf")
            total_pages     = len(doc)
            collected_slips = []

            st.markdown("""
            <div class="sp">
                <div class="sp-tag">
                    <span class="sp-num">SYS</span>
                    <span class="sp-title">Live Processing Feed</span>
                </div>
            """, unsafe_allow_html=True)

            progress_bar  = st.progress(0)
            progress_text = st.empty()
            log_container = st.expander("Operation Log", expanded=True)
            log_entries   = []

            st.markdown("</div>", unsafe_allow_html=True)

            for i in range(total_pages):
                progress_bar.progress((i + 1) / total_pages)
                progress_text.text(
                    f"[ SCAN ]  Page {i+1:04d} / {total_pages:04d}"
                    f"  ·  Captured: {len(collected_slips)}"
                )

                page    = doc[i]
                p_w     = page.rect.width
                p_h     = page.rect.height
                third_h = p_h / 3

                sections = [
                    fitz.Rect(0, 0,          p_w, third_h),
                    fitz.Rect(0, third_h,    p_w, third_h * 2),
                    fitz.Rect(0, third_h * 2, p_w, p_h),
                ]

                for idx, clip_rect in enumerate(sections):
                    section_text = page.get_text("text", clip=clip_rect)
                    match = re.search(
                        r"Booking Date\s*:\s*(\d{2}-\d{2}-\d{4})", section_text
                    )
                    if match:
                        date_str = match.group(1)
                        try:
                            curr_date = datetime.strptime(date_str, "%d-%m-%Y")
                            if start_date <= curr_date <= end_date:
                                collected_slips.append({
                                    "date":        curr_date,
                                    "page_index":  i,
                                    "section_idx": idx,
                                })
                                pos = ["TOP", "MID", "BTM"][idx]
                                log_entries.append(
                                    f"  ✦  PG {i+1:04d} [{pos}]"
                                    f"  →  {date_str}  ·  INVOICE CAPTURED"
                                )
                                log_container.text("\n".join(log_entries[-10:]))
                        except Exception:
                            continue

            collected_slips.sort(key=lambda x: x["date"])

            if collected_slips:
                out_doc = fitz.open()

                for j in range(0, len(collected_slips), 3):
                    new_page = out_doc.new_page(width=595, height=842)
                    batch    = collected_slips[j : j + 3]

                    for index, item in enumerate(batch):
                        src_page = doc[item["page_index"]]
                        s_top    = item["section_idx"]       * (src_page.rect.height / 3)
                        s_bottom = (item["section_idx"] + 1) * (src_page.rect.height / 3)
                        source_rect = fitz.Rect(0, s_top, src_page.rect.width, s_bottom)
                        t_top    = index       * (842 / 3)
                        t_bottom = (index + 1) * (842 / 3)
                        target_rect = fitz.Rect(0, t_top, 595, t_bottom)
                        new_page.show_pdf_page(
                            target_rect, doc, src_page.number, clip=source_rect
                        )

                output_pdf = io.BytesIO()
                out_doc.save(output_pdf)
                output_pdf.seek(0)
                num_out_pages = len(out_doc)
                out_doc.close()

                st.markdown(f"""
                <div class="result-stats">
                    <div class="stat-tile">
                        <div class="stat-value">{total_pages}</div>
                        <div class="stat-label">Pages Scanned</div>
                    </div>
                    <div class="stat-tile">
                        <div class="stat-value">{len(collected_slips)}</div>
                        <div class="stat-label">Invoices Found</div>
                    </div>
                    <div class="stat-tile">
                        <div class="stat-value">{num_out_pages}</div>
                        <div class="stat-label">Output Pages</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.success(
                    f"⚡  EXTRACTION COMPLETE — {len(collected_slips)} invoices "
                    f"packed across {num_out_pages} A4 pages."
                )
                st.download_button(
                    "📥  DOWNLOAD PACKED PDF",
                    output_pdf,
                    f"Packed_Invoices_"
                    f"{start_str.replace('-','')}_{end_str.replace('-','')}.pdf",
                    "application/pdf",
                )
            else:
                st.error(
                    "⚠  NO INVOICES FOUND for the selected date range. "
                    "Adjust the filter and retry."
                )

            doc.close()

        except Exception as e:
            st.error(f"⚠  SYSTEM ERROR — {e}")
