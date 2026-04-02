import streamlit as st
import fitz  # PyMuPDF
import io
import re
from datetime import datetime

st.set_page_config(
    page_title="IOCL Smart Packer",
    page_icon="⛽",
    layout="centered"
)

# ── Futuristic Premium CSS ──────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@300;400;500;600;700&family=Share+Tech+Mono&family=Exo+2:wght@200;300;400;600&display=swap');

/* ── Reset & Base ── */
html, body, [class*="css"] {
    font-family: 'Exo 2', sans-serif;
}

.stApp {
    background: #020810;
    background-image:
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(0, 168, 255, 0.12) 0%, transparent 60%),
        radial-gradient(ellipse 40% 30% at 85% 80%, rgba(255, 100, 0, 0.06) 0%, transparent 50%);
    min-height: 100vh;
}

/* ── Scanline overlay ── */
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(0, 168, 255, 0.015) 2px,
        rgba(0, 168, 255, 0.015) 4px
    );
    pointer-events: none;
    z-index: 0;
}

/* ── Main container ── */
.block-container {
    max-width: 760px !important;
    padding: 2.5rem 2rem 4rem !important;
}

/* ── Header ── */
.header-block {
    text-align: center;
    margin-bottom: 2.8rem;
    position: relative;
}

.header-eyebrow {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.35em;
    color: #00a8ff;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
    opacity: 0.75;
}

.header-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 2.6rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    line-height: 1;
    background: linear-gradient(135deg, #ffffff 30%, #00a8ff 70%, #ff6400 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
}

.header-sub {
    font-family: 'Exo 2', sans-serif;
    font-size: 0.8rem;
    font-weight: 300;
    color: rgba(160, 200, 255, 0.55);
    letter-spacing: 0.08em;
    margin-top: 0.6rem;
}

.header-line {
    width: 100%;
    height: 1px;
    background: linear-gradient(90deg, transparent, #00a8ff55, #00a8ffaa, #00a8ff55, transparent);
    margin-top: 1.6rem;
    position: relative;
}

.header-line::before {
    content: '⛽';
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    background: #020810;
    padding: 0 0.8rem;
    font-size: 1rem;
}

/* ── Card panels ── */
.panel {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(0, 168, 255, 0.18);
    border-radius: 6px;
    padding: 1.6rem 1.8rem;
    margin-bottom: 1.2rem;
    position: relative;
    backdrop-filter: blur(4px);
}

.panel::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, #00a8ff, transparent);
    border-radius: 6px 6px 0 0;
}

.panel-label {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.3em;
    color: #00a8ff;
    text-transform: uppercase;
    margin-bottom: 1rem;
    opacity: 0.7;
}

/* ── Upload area ── */
[data-testid="stFileUploader"] {
    background: rgba(0, 168, 255, 0.04) !important;
    border: 1px dashed rgba(0, 168, 255, 0.35) !important;
    border-radius: 6px !important;
    transition: border-color 0.3s, background 0.3s;
}

[data-testid="stFileUploader"]:hover {
    border-color: rgba(0, 168, 255, 0.7) !important;
    background: rgba(0, 168, 255, 0.08) !important;
}

[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] p,
[data-testid="stFileUploader"] span {
    color: rgba(160, 200, 255, 0.7) !important;
    font-family: 'Exo 2', sans-serif !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input {
    background: rgba(0, 168, 255, 0.06) !important;
    border: 1px solid rgba(0, 168, 255, 0.3) !important;
    border-radius: 4px !important;
    color: #c8e8ff !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.05em;
    padding: 0.55rem 0.9rem !important;
    transition: border-color 0.25s, box-shadow 0.25s;
}

.stTextInput > div > div > input:focus {
    border-color: #00a8ff !important;
    box-shadow: 0 0 0 2px rgba(0, 168, 255, 0.15), 0 0 18px rgba(0, 168, 255, 0.12) !important;
    outline: none !important;
}

.stTextInput label {
    color: rgba(160, 210, 255, 0.65) !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.25em !important;
    text-transform: uppercase !important;
}

/* ── Button ── */
.stButton > button {
    background: linear-gradient(135deg, rgba(0,168,255,0.15) 0%, rgba(0,168,255,0.08) 100%) !important;
    border: 1px solid rgba(0, 168, 255, 0.55) !important;
    border-radius: 4px !important;
    color: #00c8ff !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    padding: 0.65rem 2.2rem !important;
    width: 100% !important;
    cursor: pointer !important;
    transition: all 0.25s !important;
    position: relative;
    overflow: hidden;
}

.stButton > button:hover {
    background: linear-gradient(135deg, rgba(0,168,255,0.28) 0%, rgba(0,168,255,0.15) 100%) !important;
    border-color: #00a8ff !important;
    box-shadow: 0 0 24px rgba(0, 168, 255, 0.3), 0 0 8px rgba(0, 168, 255, 0.2) !important;
    color: #ffffff !important;
    transform: translateY(-1px) !important;
}

.stButton > button:active {
    transform: translateY(0px) !important;
}

/* Download button accent ── orange */
[data-testid="stDownloadButton"] > button {
    background: linear-gradient(135deg, rgba(255,100,0,0.15) 0%, rgba(255,100,0,0.08) 100%) !important;
    border: 1px solid rgba(255, 100, 0, 0.55) !important;
    color: #ff8c42 !important;
}

[data-testid="stDownloadButton"] > button:hover {
    background: linear-gradient(135deg, rgba(255,100,0,0.28) 0%, rgba(255,100,0,0.15) 100%) !important;
    border-color: #ff6400 !important;
    box-shadow: 0 0 24px rgba(255, 100, 0, 0.3), 0 0 8px rgba(255, 100, 0, 0.2) !important;
    color: #ffffff !important;
}

/* ── Progress bar ── */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #004880, #00a8ff, #00d4ff) !important;
    box-shadow: 0 0 12px rgba(0, 168, 255, 0.5);
}

.stProgress > div > div {
    background: rgba(0, 168, 255, 0.1) !important;
    border: 1px solid rgba(0, 168, 255, 0.2) !important;
    border-radius: 2px !important;
    height: 6px !important;
}

/* ── Expander (log) ── */
[data-testid="stExpander"] {
    background: rgba(0, 20, 40, 0.6) !important;
    border: 1px solid rgba(0, 168, 255, 0.2) !important;
    border-radius: 6px !important;
}

[data-testid="stExpander"] summary {
    color: rgba(100, 180, 255, 0.7) !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
}

/* ── Alerts ── */
.stSuccess {
    background: rgba(0, 255, 100, 0.07) !important;
    border: 1px solid rgba(0, 255, 100, 0.3) !important;
    border-radius: 4px !important;
    color: #80ffb0 !important;
    font-family: 'Exo 2', sans-serif !important;
}

.stError {
    background: rgba(255, 50, 50, 0.07) !important;
    border: 1px solid rgba(255, 50, 50, 0.3) !important;
    border-radius: 4px !important;
    color: #ffaaaa !important;
    font-family: 'Exo 2', sans-serif !important;
}

/* ── Status text ── */
.stText, .element-container p {
    color: rgba(160, 200, 255, 0.65) !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.75rem !important;
}

/* ── Column gaps ── */
[data-testid="stHorizontalBlock"] {
    gap: 1rem;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #020810; }
::-webkit-scrollbar-thumb { background: rgba(0,168,255,0.4); border-radius: 2px; }

/* ── Stats row ── */
.stats-row {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
}

.stat-card {
    flex: 1;
    background: rgba(0, 168, 255, 0.06);
    border: 1px solid rgba(0, 168, 255, 0.2);
    border-radius: 5px;
    padding: 0.8rem 1rem;
    text-align: center;
}

.stat-value {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.8rem;
    font-weight: 700;
    color: #00c8ff;
    line-height: 1;
}

.stat-label {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.55rem;
    letter-spacing: 0.2em;
    color: rgba(100, 160, 255, 0.55);
    text-transform: uppercase;
    margin-top: 0.3rem;
}
</style>
""", unsafe_allow_html=True)


# ── Header ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-block">
    <div class="header-eyebrow">Indian Oil Corporation Ltd — Document Processing</div>
    <div class="header-title">SMART INVOICE PACKER</div>
    <div class="header-sub">High-Speed Bulk PDF Extraction &amp; A4 Packing Engine</div>
    <div class="header-line"></div>
</div>
""", unsafe_allow_html=True)


# ── Upload Panel ─────────────────────────────────────────────────────────────
st.markdown('<div class="panel"><div class="panel-label">// 01 — Document Source</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("Upload Bulk PDF", type="pdf", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)


# ── Date Range Panel ─────────────────────────────────────────────────────────
if uploaded_file:
    st.markdown('<div class="panel"><div class="panel-label">// 02 — Date Filter Range</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        start_str = st.text_input("FROM DATE (DD-MM-YYYY)", "01-03-2026")
    with col2:
        end_str = st.text_input("TO DATE (DD-MM-YYYY)", "20-03-2026")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Execute Panel ────────────────────────────────────────────────────────
    st.markdown('<div class="panel"><div class="panel-label">// 03 — Execute</div>', unsafe_allow_html=True)
    run = st.button("🚀  INITIATE EXTRACTION SEQUENCE")
    st.markdown('</div>', unsafe_allow_html=True)

    if run:
        try:
            start_date = datetime.strptime(start_str, "%d-%m-%Y")
            end_date = datetime.strptime(end_str, "%d-%m-%Y")

            file_bytes = uploaded_file.getvalue()
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            total_pages = len(doc)
            collected_slips = []

            st.markdown('<div class="panel"><div class="panel-label">// System — Live Processing Feed</div>', unsafe_allow_html=True)
            progress_bar = st.progress(0)
            progress_text = st.empty()
            log_container = st.expander("Operation Log", expanded=True)
            log_entries = []
            st.markdown('</div>', unsafe_allow_html=True)

            for i in range(total_pages):
                progress_bar.progress((i + 1) / total_pages)
                progress_text.text(f"[ SCAN ] Page {i+1:04d} / {total_pages:04d}  ·  Slips captured: {len(collected_slips)}")

                page = doc[i]
                p_width = page.rect.width
                p_height = page.rect.height
                third_h = p_height / 3

                sections = [
                    fitz.Rect(0, 0, p_width, third_h),
                    fitz.Rect(0, third_h, p_width, third_h * 2),
                    fitz.Rect(0, third_h * 2, p_width, p_height)
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
                                    "date": curr_date,
                                    "page_index": i,
                                    "section_idx": idx
                                })
                                position_name = ["TOP", "MID", "BTM"][idx]
                                log_entries.append(f"  ✦  PG {i+1:04d} [{position_name}]  →  {date_str}  ·  INVOICE CAPTURED")
                                log_container.text("\n".join(log_entries[-10:]))
                        except Exception:
                            continue

            collected_slips.sort(key=lambda x: x["date"])

            if collected_slips:
                out_doc = fitz.open()

                for j in range(0, len(collected_slips), 3):
                    new_page = out_doc.new_page(width=595, height=842)
                    batch = collected_slips[j:j+3]

                    for index, item in enumerate(batch):
                        src_page = doc[item["page_index"]]
                        s_top = item["section_idx"] * (src_page.rect.height / 3)
                        s_bottom = (item["section_idx"] + 1) * (src_page.rect.height / 3)
                        source_rect = fitz.Rect(0, s_top, src_page.rect.width, s_bottom)
                        t_top = index * (842 / 3)
                        t_bottom = (index + 1) * (842 / 3)
                        target_rect = fitz.Rect(0, t_top, 595, t_bottom)
                        new_page.show_pdf_page(target_rect, doc, src_page.number, clip=source_rect)

                output_pdf = io.BytesIO()
                out_doc.save(output_pdf)
                output_pdf.seek(0)

                num_out_pages = len(out_doc)
                out_doc.close()

                # ── Result Stats ─────────────────────────────────────────────
                st.markdown(f"""
                <div class="stats-row">
                    <div class="stat-card">
                        <div class="stat-value">{total_pages}</div>
                        <div class="stat-label">Pages Scanned</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{len(collected_slips)}</div>
                        <div class="stat-label">Invoices Found</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{num_out_pages}</div>
                        <div class="stat-label">Output Pages</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.success(f"⚡  EXTRACTION COMPLETE — {len(collected_slips)} invoices packed across {num_out_pages} A4 pages.")
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
