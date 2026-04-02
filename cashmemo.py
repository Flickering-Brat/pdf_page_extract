import streamlit as st
import fitz  # PyMuPDF
import io
import re
from datetime import datetime

st.set_page_config(page_title="IOCL Smart Packer", page_icon="⛽")

st.title("⛽ IOCL High-Speed Invoice Packer")
st.markdown("Real-time extraction and 3-per-page A4 packing.")

uploaded_file = st.file_uploader("Upload Bulk PDF", type="pdf")

if uploaded_file:
    col1, col2 = st.columns(2)
    with col1:
        start_str = st.text_input("Start Date (DD-MM-YYYY)", "01-03-2026")
    with col2:
        end_str = st.text_input("To Date (DD-MM-YYYY)", "20-03-2026")

    if st.button("🚀 Start Extraction"):
        try:
            start_date = datetime.strptime(start_str, "%d-%m-%Y")
            end_date = datetime.strptime(end_str, "%d-%m-%Y")

            file_bytes = uploaded_file.getvalue()
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            total_pages = len(doc)
            collected_slips = []
            
            # Progress Monitoring
            progress_bar = st.progress(0)
            progress_text = st.empty()
            log_container = st.expander("Operation Log", expanded=True)
            log_entries = []

            for i in range(total_pages):
                # Update visual counter
                progress_bar.progress((i + 1) / total_pages)
                progress_text.text(f"Scanning page {i+1} of {total_pages}...")

                page = doc[i]
                p_width = page.rect.width
                p_height = page.rect.height
                third_h = p_height / 3

                # Define the 3 vertical sections in PyMuPDF's top-to-bottom coordinate system
                sections = [
                    fitz.Rect(0, 0, p_width, third_h), # Top
                    fitz.Rect(0, third_h, p_width, third_h * 2), # Middle
                    fitz.Rect(0, third_h * 2, p_width, p_height) # Bottom
                ]

                # Extract text explicitly restricted to these sections to avoid ordering/splitting issues
                for idx, clip_rect in enumerate(sections):
                    section_text = page.get_text("text", clip=clip_rect)
                    # Use regex to find the date securely
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
                                position_name = ["Top", "Middle", "Bottom"][idx]
                                log_entries.append(f"✅ Page {i+1}: Invoice found for {date_str} ({position_name})")
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
                        
                        # Calculate source boundaries from original page constraints
                        s_top = item["section_idx"] * (src_page.rect.height / 3)
                        s_bottom = (item["section_idx"] + 1) * (src_page.rect.height / 3)
                        source_rect = fitz.Rect(0, s_top, src_page.rect.width, s_bottom)
                        
                        # Calculate destination boundaries on the new A4 page
                        t_top = index * (842 / 3)
                        t_bottom = (index + 1) * (842 / 3)
                        target_rect = fitz.Rect(0, t_top, 595, t_bottom)
                        
                        # Draw the section exactly into the new placement (copies vectors/fonts flawlessly)
                        new_page.show_pdf_page(target_rect, doc, src_page.number, clip=source_rect)

                output_pdf = io.BytesIO()
                out_doc.save(output_pdf)
                output_pdf.seek(0)
                out_doc.close()

                st.success(f"Task Complete! Packed {len(collected_slips)} invoices onto {len(out_doc)} pages.")
                st.download_button("📥 Download Final PDF", output_pdf, f"Packed_Invoices.pdf", "application/pdf")
            else:
                st.error("No invoices found for the selected dates.")
                
            doc.close()
        except Exception as e:
            st.error(f"Error: {e}")
