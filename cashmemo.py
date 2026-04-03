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
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@300;400;500;600;700&family=Share+Tech+Mono&family=Exo+2:ital,wght@0,200;0,300;0,400;0,600;1,300&display=swap');

/* ═══════════════════════════════════════════
   FORCE DARK THEME — overrides light mode
═══════════════════════════════════════════ */
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
[data-testid="block-container"],
.stApp,
section.main,
.main .block-container {
    background-color: #03080f !important;
    color: #c8dff5 !important;
}

[data-testid="stHeader"] {
    background-color: #03080f !important;
}

[data-testid="stSidebar"] {
    background-color: #030c16 !important;
}

[data-testid="stToolbar"],
[data-testid="stDecoration"] {
    background: transparent !important;
}

/* ═══════════════════════════════════════════
   GLOBAL BASE
═══════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"], p, div, span, label {
    font-family: 'Exo 2', sans-serif !important;
    color: #c8dff5;
}

.stApp {
    background: #03080f;
    background-image:
        radial-gradient(ellipse 90% 55% at 50% -5%,  rgba(0, 140, 255, 0.13) 0%, transparent 65%),
        radial-gradient(ellipse 45% 35% at 90% 85%,  rgba(255, 90, 0, 0.07)  0%, transparent 55%),
        radial-gradient(ellipse 30% 25% at 5%  70%,  rgba(0, 200, 255, 0.04) 0%, transparent 50%);
    min-height: 100vh;
}

/* Scanline texture */
.stApp::after {
    content: '';
    position: fixed;
    inset: 0;
    background: repeating-linear-gradient(
        0deg,
        transparent 0px,
        transparent 3px,
        rgba(0, 150, 255, 0.012) 3px,
        rgba(0, 150, 255, 0.012) 4px
    );
    pointer-events: none;
    z-index: 9999;
}

.block-container {
    max-width: 780px !important;
    padding: 2.8rem 2.2rem 5rem !important;
}

/* ═══════════════════════════════════════════
   HEADER
═══════════════════════════════════════════ */
.iocl-header {
    text-align: center;
    margin-bottom: 3rem;
    position: relative;
    padding-bottom: 2rem;
}

.iocl-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(0, 140, 255, 0.08);
    border: 1px solid rgba(0, 140, 255, 0.25);
    border-radius: 2px;
    padding: 0.28rem 0.9rem;
    margin-bottom: 1.2rem;
}

.iocl-badge-dot {
    width: 5px; height: 5px;
    background: #00a8ff;
    border-radius: 50%;
    box-shadow: 0 0 6px #00a8ff;
    animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
    0%, 100% { opacity: 1;   transform: scale(1);   }
    50%       { opacity: 0.4; transform: scale(0.7); }
}

.iocl-badge-text {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.58rem !important;
    letter-spacing: 0.32em;
    color: #00a8ff !important;
    text-transform: uppercase;
}

.iocl-title {
    font-family: 'Rajdhani', sans-serif !important;
    font-size: clamp(2rem, 5vw, 2.9rem);
    font-weight: 700;
    letter-spacing: 0.06em;
    line-height: 1;
    background: linear-gradient(140deg, #e8f4ff 15%, #5bc8ff 55%, #ff7a20 95%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 0.5rem 0;
}

.iocl-subtitle {
    font-family: 'Exo 2', sans-serif !important;
    font-size: 0.78rem;
    font-weight: 300;
    font-style: italic;
    color: rgba(140, 185, 235, 0.5) !important;
    letter-spacing: 0.12em;
    margin: 0;
}

.iocl-divider {
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg,
        transparent 0%,
        rgba(0,140,255,0.2) 15%,
        rgba(0,168,255,0.7) 50%,
        rgba(0,140,255,0.2) 85%,
        transparent 100%
    );
}

.iocl-divider::before {
    content: '';
    position: absolute;
    left: 50%; top: 50%;
    transform: translate(-50%, -50%);
    width: 6px; height: 6px;
    background: #00a8ff;
    border-radius: 50%;
    box-shadow: 0 0 12px 3px rgba(0,168,255,0.6);
}

/* ═══════════════════════════════════════════
   STEP PANELS
═══════════════════════════════════════════ */
.step-panel {
    position: relative;
    background: linear-gradient(145deg, rgba(0,140,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
    border: 1px solid rgba(0, 140, 255, 0.2);
    border-radius: 8px;
    padding: 1.5rem 1.8rem 1.6rem;
    margin-bottom: 1.1rem;
    overflow: hidden;
}

.step-panel::before {
    content: '';
    position: absolute;
    top: 0; left: 10%; right: 10%;
    height: 1px;
    background: linear-gradient(90deg, transparent, #00a8ff, transparent);
    box-shadow: 0 0 8px rgba(0,168,255,0.5);
}

.step-panel::after {
    content: '';
    position: absolute;
    bottom: 0; right: 0;
    width: 60px; height: 60px;
    background: radial-gradient(circle at bottom right, rgba(0,168,255,0.06), transparent 70%);
    border-radius: 0 0 8px 0;
}

.step-tag {
    display: flex;
    align-items: center;
    gap: 0.55rem;
    margin-bottom: 1.1rem;
}

.step-num {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.58rem !important;
    color: #00a8ff !important;
    background: rgba(0,168,255,0.1);
    border: 1px solid rgba(0,168,255,0.3);
    border-radius: 2px;
    padding: 0.15rem 0.45rem;
    letter-spacing: 0.1em;
}

.step-title {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.6rem !important;
    letter-spacing: 0.28em;
    color: rgba(120,175,230,0.6) !important;
    text-transform: uppercase;
}

/* ═══════════════════════════════════════════
   FILE UPLOADER — suppress built-in label
═══════════════════════════════════════════ */
[data-testid="stFileUploader"] > label {
    display: none !important;
}

[data-testid="stFileUploader"] section {
    background: rgba(0, 140, 255, 0.04) !important;
    border: 1px dashed rgba(0, 140, 255, 0.4) !important;
    border-radius: 6px !important;
    padding: 1.6rem !important;
    transition: all 0.3s ease;
}

[data-testid="stFileUploader"] section:hover {
    border-color: rgba(0, 168, 255, 0.75) !important;
    background: rgba(0, 140, 255, 0.09) !important;
    box-shadow: 0 0 20px rgba(0,168,255,0.08) inset !important;
}

[data-testid="stFileUploader"] section * {
    color: rgba(140, 190, 240, 0.7) !important;
    font-family: 'Exo 2', sans-serif !important;
}

[data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] {
    background: rgba(0, 140, 255, 0.1) !important;
    border: 1px solid rgba(0, 168, 255, 0.35) !important;
    border-radius: 4px !important;
}

/* ═══════════════════════════════════════════
   TEXT INPUTS
═══════════════════════════════════════════ */
.stTextInput label {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.6rem !important;
    letter-spacing: 0.28em !important;
    text-transform: uppercase !important;
    color: rgba(120, 175, 230, 0.6) !important;
    margin-bottom: 0.4rem !important;
}

.stTextInput input {
    background: rgba(0, 140, 255, 0.07) !important;
    border: 1px solid rgba(0, 140, 255, 0.28) !important;
    border-radius: 5px !important;
    color: #aee0ff !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 1rem !important;
    letter-spacing: 0.08em !important;
    padding: 0.6rem 1rem !important;
    transition: border-color 0.2s, box-shadow 0.2s, background 0.2s;
}

.stTextInput input:focus {
    border-color: rgba(0, 168, 255, 0.8) !important;
    background: rgba(0, 140, 255, 0.12) !important;
    box-shadow: 0 0 0 3px rgba(0,168,255,0.1), 0 0 20px rgba(0,168,255,0.1) !important;
    outline: none !important;
}

.stTextInput input::placeholder {
    color: rgba(100, 160, 210, 0.35) !important;
}

/* ═══════════════════════════════════════════
   BUTTONS
═══════════════════════════════════════════ */
.stButton button {
    width: 100% !important;
    background: linear-gradient(135deg,
        rgba(0, 140, 255, 0.18) 0%,
        rgba(0, 100, 200, 0.1) 100%) !important;
    border: 1px solid rgba(0, 168, 255, 0.5) !important;
    border-radius: 5px !important;
    color: #5cd0ff !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    padding: 0.7rem 1.5rem !important;
    cursor: pointer !important;
    transition: all 0.22s ease !important;
}

.stButton button:hover {
    border-color: rgba(0, 200, 255, 0.85) !important;
    color: #ffffff !important;
    box-shadow:
        0 0 0 1px rgba(0,200,255,0.2),
        0 0 28px rgba(0,168,255,0.25),
        0 4px 16px rgba(0,0,0,0.4) !important;
    transform: translateY(-2px) !important;
}

.stButton button:active {
    transform: translateY(0) !important;
}

[data-testid="stDownloadButton"] button {
    background: linear-gradient(135deg,
        rgba(255, 100, 0, 0.18) 0%,
        rgba(200, 70, 0, 0.1) 100%) !important;
    border: 1px solid rgba(255, 110, 0, 0.5) !important;
    color: #ffaa55 !important;
}

[data-testid="stDownloadButton"] button:hover {
    border-color: rgba(255, 140, 0, 0.9) !important;
    color: #ffffff !important;
    box-shadow:
        0 0 0 1px rgba(255,120,0,0.2),
        0 0 28px rgba(255,100,0,0.25),
        0 4px 16px rgba(0,0,0,0.4) !important;
}

/* ═══════════════════════════════════════════
   PROGRESS BAR
═══════════════════════════════════════════ */
.stProgress > div > div {
    background: rgba(0, 140, 255, 0.12) !important;
    border: 1px solid rgba(0, 140, 255, 0.22) !important;
    border-radius: 3px !important;
    height: 5px !important;
}

.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #003d7a, #0090e0, #00d4ff) !important;
    box-shadow: 0 0 10px rgba(0, 200, 255, 0.55) !important;
    border-radius: 3px !important;
}

/* ═══════════════════════════════════════════
   EXPANDER / LOG
═══════════════════════════════════════════ */
[data-testid="stExpander"] {
    background: rgba(0, 15, 35, 0.7) !important;
    border: 1px solid rgba(0, 140, 255, 0.2) !important;
    border-radius: 6px !important;
}

[data-testid="stExpander"] details > summary {
    color: rgba(100, 175, 240, 0.65) !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.62rem !important;
    letter-spacing: 0.25em !important;
    text-transform: uppercase !important;
    padding: 0.7rem 1rem !important;
}

/* ═══════════════════════════════════════════
   ALERTS
═══════════════════════════════════════════ */
[data-testid="stAlert"] {
    border-radius: 5px !important;
    font-family: 'Exo 2', sans-serif !important;
}

/* ═══════════════════════════════════════════
   STATUS TEXT
═══════════════════════════════════════════ */
.stText p, .element-container > div > p {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.72rem !important;
    color: rgba(120, 175, 230, 0.6) !important;
    line-height: 1.6;
}

/* ═══════════════════════════════════════════
   STATS CARDS
═══════════════════════════════════════════ */
.result-stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.9rem;
    margin: 1.4rem 0 1.2rem;
}

.stat-tile {
    background: linear-gradient(145deg, rgba(0,140,255,0.08), rgba(0,80,160,0.04));
    border: 1px solid rgba(0, 140, 255, 0.22);
    border-radius: 6px;
    padding: 1rem 0.8rem;
    text-align: center;
    position: relative;
    overflow: hidden;
}

.stat-tile::before {
    content: '';
    position: absolute;
    top: 0; left: 20%; right: 20%;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0,168,255,0.6), transparent);
}

.stat-tile-value {
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 2.1rem;
    font-weight: 700;
    color: #3dcfff !important;
    line-height: 1;
    text-shadow: 0 0 20px rgba(0,200,255,0.4);
}

.stat-tile-label {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.52rem !important;
    letter-spacing: 0.22em;
    color: rgba(100, 160, 220, 0.5) !important;
    text-transform: uppercase;
    margin-top: 0.3rem;
}

/* ═══════════════════════════════════════════
   MISC
═══════════════════════════════════════════ */
[data-testid="stHorizontalBlock"] { gap: 1rem; }

::-webkit-scrollbar { width: 3px; height: 3px; }
::-webkit-scrollbar-track { background: #03080f; }
::-webkit-scrollbar-thumb { background: rgba(0,168,255,0.35); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: rgba(0,168,255,0.6); }
</style>
""", unsafe_allow_html=True)


# ── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="iocl-header">
    <div style="display:flex;justify-content:center;margin-bottom:1.1rem;">
        <div class="iocl-badge">
            <div class="iocl-badge-dot"></div>
            <span class="iocl-badge-text">Indian Oil Corporation Ltd &nbsp;·&nbsp; Invoice Editor</span>
        </div>
    </div>
    <div class="iocl-title">SMART INVOICE EXTRACTOR</div>
    <p class="iocl-subtitle">High-Speed Bulk PDF Extraction &amp; A4 Packing Engine</p>
    <div class="iocl-divider"></div>
</div>
""", unsafe_allow_html=True)


# ── PANEL 01 — UPLOAD ────────────────────────────────────────────────────────
st.markdown("""
<div class="step-panel">
    <div class="step-tag">
        <span class="step-num">01</span>
        <span class="step-title">Document Source</span>
    </div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Drop your bulk PDF here",
    type="pdf",
    label_visibility="collapsed"
)

st.markdown("</div>", unsafe_allow_html=True)


# ── PANELS 02 & 03 ───────────────────────────────────────────────────────────
if uploaded_file:

    st.markdown("""
    <div class="step-panel">
        <div class="step-tag">
            <span class="step-num">02</span>
            <span class="step-title">Date Filter Range</span>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        start_str = st.text_input("From Date (DD-MM-YYYY)", "01-03-2026")
    with col2:
        end_str = st.text_input("To Date (DD-MM-YYYY)", "20-03-2026")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="step-panel">
        <div class="step-tag">
            <span class="step-num">03</span>
            <span class="step-title">Execute</span>
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
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            total_pages = len(doc)
            collected_slips = []

            st.markdown("""
            <div class="step-panel">
                <div class="step-tag">
                    <span class="step-num">SYS</span>
                    <span class="step-title">Live Processing Feed</span>
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
                    f"[ SCAN ]  Page {i+1:04d} / {total_pages:04d}  ·  Captured: {len(collected_slips)}"
                )

                page    = doc[i]
                p_w     = page.rect.width
                p_h     = page.rect.height
                third_h = p_h / 3

                sections = [
                    fitz.Rect(0, 0,         p_w, third_h),
                    fitz.Rect(0, third_h,   p_w, third_h * 2),
                    fitz.Rect(0, third_h*2, p_w, p_h)
                ]

                for idx, clip_rect in enumerate(sections):
                    section_text = page.get_text("text", clip=clip_rect)
                    match = re.search(r"Booking Date\s*:\s*(\d{2}-\d{2}-\d{4})", section_text)
                    if match:
                        date_str = match.group(1)
                        try:
                            curr_date = datetime.strptime(date_str, "%d-%m-%Y")
                            if start_date <= curr_date <= end_date:
                                collected_slips.append({
                                    "date":        curr_date,
                                    "page_index":  i,
                                    "section_idx": idx
                                })
                                pos = ["TOP", "MID", "BTM"][idx]
                                log_entries.append(
                                    f"  ✦  PG {i+1:04d} [{pos}]  →  {date_str}  ·  CAPTURED"
                                )
                                log_container.text("\n".join(log_entries[-10:]))
                        except Exception:
                            continue

            collected_slips.sort(key=lambda x: x["date"])

            if collected_slips:
                out_doc = fitz.open()

                for j in range(0, len(collected_slips), 3):
                    new_page = out_doc.new_page(width=595, height=842)
                    batch    = collected_slips[j:j+3]

                    for index, item in enumerate(batch):
                        src_page = doc[item["page_index"]]
                        s_top    = item["section_idx"]     * (src_page.rect.height / 3)
                        s_bottom = (item["section_idx"]+1) * (src_page.rect.height / 3)
                        source_rect = fitz.Rect(0, s_top, src_page.rect.width, s_bottom)
                        t_top    = index     * (842 / 3)
                        t_bottom = (index+1) * (842 / 3)
                        target_rect = fitz.Rect(0, t_top, 595, t_bottom)
                        new_page.show_pdf_page(target_rect, doc, src_page.number, clip=source_rect)

                output_pdf = io.BytesIO()
                out_doc.save(output_pdf)
                output_pdf.seek(0)
                num_out_pages = len(out_doc)
                out_doc.close()

                st.markdown(f"""
                <div class="result-stats">
                    <div class="stat-tile">
                        <div class="stat-tile-value">{total_pages}</div>
                        <div class="stat-tile-label">Pages Scanned</div>
                    </div>
                    <div class="stat-tile">
                        <div class="stat-tile-value">{len(collected_slips)}</div>
                        <div class="stat-tile-label">Invoices Found</div>
                    </div>
                    <div class="stat-tile">
                        <div class="stat-tile-value">{num_out_pages}</div>
                        <div class="stat-tile-label">Output Pages</div>
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
                    f"Packed_Invoices_{start_str.replace('-','')}_{end_str.replace('-','')}.pdf",
                    "application/pdf"
                )
            else:
                st.error("⚠  NO INVOICES FOUND for the selected date range. Adjust filter and retry.")

            doc.close()

        except Exception as e:
            st.error(f"⚠  SYSTEM ERROR — {e}")
